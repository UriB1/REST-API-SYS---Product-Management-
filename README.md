# REST API System for Product Management

## General Description

This project involves developing a REST API system for managing products using Flask. The backend server provides API endpoints for user management and product operations. Firebase Realtime Database is used for storing product data, and Firebase Authentication handles user authentication. The system allows users to register, upload, retrieve, update, and delete products, and view products uploaded by other users.

## Functionality Requirements

### User Registration

- **Endpoint:** [POST] `/register`
- **Description:** Allows a user to register with an email and password. User details are stored in Firebase Authentication, and additional information is saved in Firebase Realtime Database.

### Product Upload

- **Endpoint:** [POST] `/upload_product`
- **Description:** Authenticated users can upload new products. The product data is saved in Firebase Realtime Database with a reference to the user who created it.

### Retrieve User Products

- **Endpoint:** [GET] `/user_products`
- **Description:** Retrieves all products uploaded by the authenticated user. Uses a simple cache mechanism for the results.

### Delete Product

- **Endpoint:** [DELETE] `/delete_product/<product_id>`
- **Description:** Allows a user to delete a product they have uploaded.

### Product Information

- **Endpoint:** [GET] `/product_info/<product_id>`
- **Description:** Any user can retrieve detailed information about a specific product using its unique identifier (`product_id`).

### Retrieve All Products

- **Endpoint:** [GET] `/all_products`
- **Description:** Allows any user to view all products available in the system.

### Update Product

- **Endpoint:** [PUT] `/update_product/<product_id>`
- **Description:** Allows a user to update details of a product they have uploaded.

### Search Products

- **Endpoint:** [GET] `/search_products?query=<search_query>`
- **Description:** Enables users to search for products using specific keywords.

### Filter Products by Category

- **Endpoint:** [GET] `/products_by_category/<category_name>`
- **Description:** Retrieves products that belong to a specific category.

## Key Points for Execution

- **Authentication:** All endpoints are secured using Firebase Authentication to ensure that only registered and authenticated users can perform actions on products.
- **Authorization:** Only the user who uploaded a product can update or delete it.
- **Validation:** All incoming data is validated to ensure it meets the required format before being stored in Firebase Realtime Database.
- **Error Handling:** Proper error handling is implemented for authentication errors, authorization issues, and general exceptions.

## Tools and Frameworks

- **Flask:** A lightweight WSGI web application framework for developing the REST API.
- **Firebase Realtime Database:** For storing and retrieving product data.
- **Firebase Authentication:** For managing and authenticating users.

## Getting Started

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo.git

2. **Navigate to the Project Directory:**
   ```bash
   cd your-repo

3. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt

5. **Obtain Firebase Credentials:**
   - Register or sign in to your Firebase account.
   - Download your serviceAccountKey.json file from the Firebase Console:
      - Go to the Firebase Console.
      - Select your project.
      - Navigate to Project Settings > Service accounts.
      - Click "Generate new private key" to download the serviceAccountKey.json file.
   - Place the serviceAccountKey.json file in the project root directory.

6. **Set Up Environment Variables:**
   - Create a .env file in the project root with necessary environment variables. Ensure that it includes the path to your serviceAccountKey.json file and any other configuration values required by your application.

7. **Run the Flask Application:**
   ```bash
   python app.py

8. **Access the API:**
   - Use tools like Postman to interact with the API endpoints.
