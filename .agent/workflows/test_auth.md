---
description: Test the Real World Authentication Flow (Register -> Login)
---

This workflow tests the secure authentication implementation.

1.  **Preparation**: Ensure containers are running.
    ```bash
    docker-compose ps
    ```

2.  **Access Frontend**: Open browser at `http://localhost:3000`.

3.  **Test Registration**:
    *   Click "Register" link at bottom of form.
    *   Enter Username: `secure_user_1`
    *   Enter Password: `password123`
    *   Click "Register" button.
    *   Expected: Success message "Registration successful!" and auto-login.

4.  **Test Logout**:
    *   Click "Logout" button in header.
    *   Expected: Return to Login form.

5.  **Test Login (Success)**:
    *   Enter Username: `secure_user_1`
    *   Enter Password: `password123`
    *   Click "Login".
    *   Expected: Successful login to Flash Sale page.

6.  **Test Login (Failure - Wrong Password)**:
    *   Logout again.
    *   Enter Username: `secure_user_1`
    *   Enter Password: `wrongpassword`
    *   Click "Login".
    *   Expected: Error "Invalid username or password".

7.  **Test Login (Failure - Unregistered User)**:
    *   Enter Username: `non_existent_user`
    *   Enter Password: `password123`
    *   Click "Login".
    *   Expected: Error "Invalid username or password".
