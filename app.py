import firebase_admin
import logging
import utils

from firebase_admin import credentials, auth, db
from flask import Flask, request, jsonify
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config
from utils import auth_required


app = Flask(__name__)
app.config.from_object(Config)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Simple in-memory cache
cache.init_app(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(app.config['FIREBASE_SERVICE_ACCOUNT_KEY'])
firebase_admin.initialize_app(cred, {'databaseURL': app.config['FIREBASE_DB_URL']})
auth_client = auth  # Firebase Admin SDK auth module for user management

# User Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Validate email and password
        if not utils.validate_email_format(email) or not utils.validate_password_strength(password):
            return jsonify({'error': 'Invalid email or weak password format'}), 400

        try:
            user = auth.create_user(
                email=email,
                password=password
            )
            user_id = user.uid
            db.reference(f'users/{user_id}').set({
                'email': email,
                'user_id': user_id,
            })
            return jsonify({'message': 'User registered successfully'}), 201
        except Exception as e:
            logging.error(f'Error during user registration: {str(e)}')
            return jsonify({'error': 'An error occurred while registering the user'}), 400

# Product Upload Endpoint
product_ref = db.reference('products')
@app.route('/upload_product', methods=['POST'])
@auth_required(auth_client)
def upload_product():
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']
        data = request.get_json()
        if 'required_field' not in data:
            return jsonify({'error': 'Required field missing'}), 400
        data['user_id'] = user_id
        product_id = product_ref.push().key
        data['product_id'] = product_id
        product_ref.child(product_id).set(data)
        logging.info(f"Request IP: {get_remote_address()}")
        return jsonify({'message': 'Product uploaded successfully'}), 201
    except Exception as e:
        return jsonify({'error': 'An error occurred while uploading the product'}), 500

# Retrieve User Products Endpoint
@app.route('/user_products', methods=['GET'])
@auth_required(auth_client)
def user_products():
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']
        app.logger.info(f"Request IP: {get_remote_address()}")

        # Cache key
        cache_key = 'user_products_' + user_id

        # Get or set cached products
        products = cache.get(cache_key)
        if products is None:
            products = db.reference('products').order_by_child('user_id').equal_to(user_id).get()
            cache.set(cache_key, products)

        return jsonify(products), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'error': 'Invalid or missing token'}), 400

# Delete Product Endpoint
@app.route('/delete_product/<product_id>', methods=['DELETE'])
@auth_required(auth_client)
def delete_product(product_id):
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        if not token:
            return jsonify({'error': 'Empty or malformed token'}), 403
        user = auth.verify_id_token(token)
        user_id = user['uid']
        product_ref = db.reference(f'products/{product_id}')
        product = product_ref.get()
        if product and 'user_id' in product and product['user_id'] == user_id:
            logging.info(f"Product with ID {product_id} deleted by user {user_id}")
            product_ref.delete()
            return jsonify({'message': 'Product deleted successfully'}), 200
        else:
            logging.error(f"Unauthorized deletion attempt for product with ID {product_id} by user {user_id}")
            return jsonify({'error': 'Unauthorized'}), 403
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while deleting the product'}), 500

# Product Information Endpoint
@app.route('/product_info/<product_id>', methods=['GET'])
@auth_required(auth_client)
def product_info(product_id):
    try:
        if not product_id.isnumeric():
            return jsonify({'error': 'Invalid product ID format'}), 400
        product = db.reference(f'products/{product_id}').get()
        if product:
            app.logger.info(f"Product with ID {product_id} accessed successfully.")
            return jsonify(product), 200
        else:
            app.logger.error(f"Product with ID {product_id} not found.")
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        app.logger.error(f"An error occurred while accessing the database: {str(e)}")
        return jsonify({'error': 'An error occurred while accessing the database'}), 500

# Retrieve All Products Endpoint
@app.route('/all_products', methods=['GET'])
@auth_required(auth_client)
def all_products():
    app.logger.info('Accessed all_products endpoint')
    try:
        products = db.reference('products').get()
        app.logger.debug(f'Retrieved products: {products}')
        if products is not None and isinstance(products, dict):
            return jsonify(products), 200
        else:
            return jsonify({"error": "Invalid data retrieved"}), 500
    except Exception as e:
        app.logger.error(f'An error occurred: {str(e)}')
        return jsonify({'error': 'An error occurred while fetching products'}), 500

# Update Product Endpoint
@app.route('/update_product/<product_id>', methods=['PUT'])
@auth_required(auth_client)
def update_product(product_id):
    try:
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']
        product_ref = db.reference(f'products/{product_id}')
        product = product_ref.get()

        if not product:
            logging.error('Product not found')
            return jsonify({'error': 'Product not found'}), 404

        if product['user_id'] != user_id:
            logging.error('Unauthorized access to update product')
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.get_json()
        product_ref.update(data)
        logging.info('Product updated successfully')
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while updating the product'}), 500

# Search Products Endpoint
@app.route('/search_products', methods=['GET'])
@cache.cached(timeout=300, key_prefix='search_results')
@auth_required(auth_client)
def search_products():
    query = request.args.get('query')
    if not isinstance(query, str):
        return jsonify({'error': 'Search query is required'}), 400
    query = query.strip()  # Sanitize input

    logging.info(f"Search query: {query}")
    products = db.reference('products').order_by_child('title').equal_to(query.lower()).get()
    logging.info(f"Search results: {products}")

    return jsonify(products), 200

# Filter Products by Category Endpoint
@app.route('/products_by_category/<category_name>', methods=['GET'])
@auth_required(auth_client)
def products_by_category(category_name):
    try:
        app.logger.info(f'Request received for category: {category_name}')
        products = db.reference('products').order_by_child('category').equal_to(category_name).get()
        if not products:
            return jsonify({'error': 'No products found for the given category'}), 404
        app.logger.info(f'Response sent for category: {category_name}')
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': 'An error occurred while fetching products'}), 500

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
