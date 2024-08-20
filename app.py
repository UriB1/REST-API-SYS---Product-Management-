import firebase_admin
import logging
import utils

from firebase_admin import credentials, auth, db
from flask import Flask, request, jsonify
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from config import Config
from utils import auth_required

# Initialize Flask application
app = Flask(__name__)

# Load configuration from the Config class
app.config.from_object(Config)

# Initialize cache with simple in-memory cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Initialize Firebase Admin SDK with service account credentials
cred = credentials.Certificate(app.config['FIREBASE_SERVICE_ACCOUNT_KEY'])
firebase_admin.initialize_app(cred, {'databaseURL': app.config['FIREBASE_DB_URL']})

# Firebase authentication client
auth_client = auth  # Firebase Admin SDK auth module for user management

# User Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Validate email and password format
        if not utils.validate_email_format(email) or not utils.validate_password_strength(password):
            return jsonify({'error': 'Invalid email or weak password format'}), 400

        try:
            # Create a new user in Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password
            )
            user_id = user.uid
            # Store user details in Firebase Realtime Database
            db.reference(f'users/{user_id}').set({
                'email': email,
                'user_id': user_id,
            })
            return jsonify({'message': 'User registered successfully'}), 201
        
        except auth.EmailAlreadyExistsError:
            logging.error(f'Error: Email {email} already exists.')
            return jsonify({'error': 'Email already exists. Please use a different email address.'}), 400

        except Exception as e:
            logging.error(f'Error during user registration: {str(e)}')
            return jsonify({'error': 'An error occurred while registering the user'}), 400

# Product Upload Endpoint
product_ref = db.reference('products')
@app.route('/upload_product', methods=['POST'])
@auth_required(auth_client)
def upload_product():
    try:
        # Extract and verify the authorization token
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']
        
        # Get the product data from the request
        data = request.get_json()
        if 'required_field' not in data:
            return jsonify({'error': 'Required field missing'}), 400
        
        # Add user ID to the product data
        data['user_id'] = user_id
        product_id = product_ref.push().key  # Generate a new product ID
        data['product_id'] = product_id
        # Store the product data in Firebase Realtime Database
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
        # Extract and verify the authorization token
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']
        app.logger.info(f"Request IP: {get_remote_address()}")

        # Cache key for user products
        cache_key = 'user_products_' + user_id

        # Try to get cached products
        products = cache.get(cache_key)
        if products is None:
            # Fetch user products from Firebase Realtime Database
            products = db.reference('products').order_by_child('user_id').equal_to(user_id).get()
            cache.set(cache_key, products)  # Cache the products

        return jsonify(products), 200
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'error': 'Invalid or missing token'}), 400

# Delete Product Endpoint
@app.route('/delete_product/<product_id>', methods=['DELETE'])
@auth_required(auth_client)
def delete_product(product_id):
    try:
        # Extract and verify the authorization token
        token = request.headers.get('Authorization', '').split(' ')[1]
        if not token:
            return jsonify({'error': 'Empty or malformed token'}), 403
        user = auth.verify_id_token(token)
        user_id = user['uid']

        product_ref = db.reference(f'products/{product_id}')
        product = product_ref.get()

        if product is None:
            # Product does not exist
            return jsonify({'error': f'Product with ID {product_id} does not exist'}), 404

        if 'user_id' in product and product['user_id'] == user_id:
            # Delete the product if it belongs to the user
            logging.info(f"Product with ID {product_id} deleted by user {user_id}")
            product_ref.delete()
            return jsonify({'message': f'Product with ID {product_id} deleted successfully'}), 200
        else:
            # Unauthorized access attempt
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
        product = db.reference(f'products/{product_id}').get()
        
        if product:
            app.logger.info(f"Product with ID {product_id} accessed successfully.")
            return jsonify(product), 200
        else:
            app.logger.error(f"Product with ID {product_id} not found.")
            return jsonify({'error': f'Product with ID {product_id} not found'}), 404
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
        
        if products is not None and isinstance(products, dict) and products:
            return jsonify(products), 200
        elif products == {}:
            return jsonify({"message": "No products available"}), 200
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
        # Extract and verify the authorization token
        token = request.headers.get('Authorization', '').split(' ')[1]
        user = auth.verify_id_token(token)
        user_id = user['uid']

        # Reference the product from the database
        product_ref = db.reference(f'products/{product_id}')
        product = product_ref.get()

        if not product:
            logging.error(f'Product with ID {product_id} not found.')
            return jsonify({'error': 'Product not found'}), 404

        if product['user_id'] != user_id:
            logging.error(f'Unauthorized update attempt on product {product_id} by user {user_id}')
            return jsonify({'error': 'Unauthorized'}), 403

        # Get the updated data from the request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided for update'}), 400

        # Update the product with new data
        product_ref.update(data)
        logging.info(f'Product with ID {product_id} updated successfully by user {user_id}')
        return jsonify({'message': 'Product updated successfully'}), 200

    except Exception as e:
        logging.error(f'An error occurred: {str(e)}')
        return jsonify({'error': 'An error occurred while updating the product'}), 500

# Search Products Endpoint
@app.route('/search_products', methods=['GET'])
@auth_required(auth_client)
def search_products():
    query = request.args.get('query')

    # Validate search query
    if not query or not isinstance(query, str):
        return jsonify({'error': 'Search query is required and should be a string'}), 400

    query = query.strip()  # Sanitize and standardize the query input

    logging.info(f"Search query: {query}")

    try:
        # Perform the search in the Firebase Realtime Database based on the title
        products = db.reference('products').order_by_child('title').equal_to(query).get()

        if products:
            logging.info(f"Search results for query '{query}': {products}")
            return jsonify(products), 200
        else:
            logging.info(f"No products found for query '{query}'")
            return jsonify({'message': f"No products found for query '{query}'"}), 404

    except Exception as e:
        logging.error(f"An error occurred while searching for products: {str(e)}")
        return jsonify({'error': 'An error occurred while searching for products'}), 500

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

# Main entry point of the application
if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask application in debug mode
