# Authentication API Doc

## Base Path

```text
/api/v1/auth
```

---

## 1. Google Login

### `GET /api/v1/auth/login/google/`

Initiates the OAuth 2.0 / OpenID Connect authorization flow with Google.

### Parameters

| Name | Location | Type | Required | Default | Validation & Behavior |
|------|----------|------|----------|---------|-----------------------|
| `return_to` | Query | `string` | Optional | `"/"` | Must start with `/` and must **not** start with `//`. Sanitized via `validate_return_to()`. If omitted, empty, or invalid, safely falls back to `"/"`. |

### Execution Flow

1. Validates the `return_to` query parameter.
2. Stores `return_to` inside the temporary encrypted Starlette session cookie.
3. Generates the Google OAuth authorization URL requesting scopes `openid email profile` with PKCE (`code_challenge_method="S256"`).
4. Issues an HTTP `302 Found` redirect sending the browser to Google's sign-in screen.

### Request

```http
GET /api/v1/auth/login/google/?return_to=/create-qr HTTP/1.1
Host: api.inoqr.org
```

### Response

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=...&redirect_uri=https%3A%2F%2Fapi.inoqr.org%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback%2F&scope=openid+email+profile&state=...&code_challenge=...&code_challenge_method=S256
Set-Cookie: session=...; Path=/; HttpOnly; SameSite=lax
```

---

## 2. GitHub Login

### `GET /api/v1/auth/login/github/`

Initiates the OAuth 2.0 authorization flow with GitHub.

### Parameters

| Name | Location | Type | Required | Default | Validation & Behavior |
|------|----------|------|----------|---------|-----------------------|
| `return_to` | Query | `string` | Optional | `"/"` | Must start with `/` and must **not** start with `//`. Sanitized via `validate_return_to()`. If omitted, empty, or invalid, safely falls back to `"/"`. |

### Execution Flow

1. Validates the `return_to` query parameter.
2. Stores `return_to` inside the temporary encrypted Starlette session cookie.
3. Generates the GitHub OAuth authorization URL requesting scope `user` with PKCE (`code_challenge_method="S256"`) and `prompt="select_account"`.
4. Issues an HTTP `302 Found` redirect sending the browser to GitHub's authorization screen.

### Request

```http
GET /api/v1/auth/login/github/?return_to=/dashboard HTTP/1.1
Host: api.inoqr.org
```

### Response

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?response_type=code&client_id=...&redirect_uri=https%3A%2F%2Fapi.inoqr.org%2Fapi%2Fv1%2Fauth%2Fgithub%2Fcallback%2F&scope=user%3Aemail&state=...&code_challenge=...&code_challenge_method=S256&prompt=select_account
Set-Cookie: session=...; Path=/; HttpOnly; SameSite=lax
```

---

## 3. Google OAuth Callback

### `GET /api/v1/auth/google/callback/`

Handles the incoming redirect from Google following user authorization. Exchanges the authorization code for tokens, verifies identity, provisions the user account, establishes a persistent InoQR session, and redirects the browser back to the frontend.

### Parameters

Supplied by Google in the query string:

| Name | Location | Type | Description |
|------|----------|------|-------------|
| `code` | Query | `string` | OAuth authorization code issued by Google. |
| `state` | Query | `string` | Anti-CSRF OAuth state token validated against the session cookie. |
| `session` | Cookie | `string` | Starlette OAuth session cookie containing OAuth state and PKCE verifier. |

### Execution Flow

1. **Token Exchange:** Exchanges `code` and verifies `state` and PKCE code challenge with Google.
2. **Profile Extraction:** Extracts identity claims from the OpenID Connect token (`token["userinfo"]`):
   - `sub` &rarr; `provider_user_id`
   - `name` &rarr; `name`
   - `email` &rarr; `email`
   - `picture` &rarr; `image_url`
3. **User Provisioning:** Searches for an existing user where `provider = 'google'` and `provider_user_id = sub`. If not found, inserts a new user record.
4. **Session Creation:** Creates a 32-byte URL-safe cryptographic session token, persists its SHA-256 hash in the database `sessions` table with a 7-day lifetime, and issues the plaintext token in a cookie.
5. **Redirect Destination:** Reads and removes `return_to` from the OAuth session (defaults to `"/"`).
6. **Frontend Redirect:** Redirects browser to `{FRONTEND_URL}{return_to}` with the session cookie attached.

### Success Response

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/create-qr
Set-Cookie: __Host-inoqr_session_id=pA4q8jX_k9Lm...; Max-Age=604800; Path=/; SameSite=strict; Secure; HttpOnly
```

### Failure Response

On authentication failures (invalid state, rejected consent, expired code, or missing token):

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/?error=authentication_failed
```

On unhandled server exceptions (database failure, missing profile fields, or network failure):

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/?error=server_error
```

*Note: OAuth callback failures always return browser redirects to the frontend root with an `error` query parameter. They never return JSON responses.*

---

## 4. GitHub OAuth Callback

### `GET /api/v1/auth/github/callback/`

Handles the incoming redirect from GitHub following user authorization. Exchanges the authorization code for an access token, queries GitHub for user profile and verified email, provisions the user, establishes a persistent InoQR session, and redirects to the frontend.

### Parameters

Supplied by GitHub in the query string:

| Name | Location | Type | Description |
|------|----------|------|-------------|
| `code` | Query | `string` | OAuth authorization code issued by GitHub. |
| `state` | Query | `string` | Anti-CSRF OAuth state token validated against the session cookie. |
| `session` | Cookie | `string` | Starlette OAuth session cookie containing OAuth state and PKCE verifier. |

### Execution Flow

1. **Token Exchange:** Exchanges `code` and verifies `state` and PKCE code challenge with GitHub.
2. **Profile Retrieval:** Calls GitHub API `GET https://api.github.com/user`:
   - `id` &rarr; stringified to `provider_user_id`
   - `name` &rarr; `name`
   - `avatar_url` &rarr; `image_url`
3. **Email Verification:** Calls GitHub API `GET https://api.github.com/user/emails`:
   - Iterates through account emails to find an entry where `primary == true` and `verified == true`.
   - **Crucial Requirement:** If no primary verified email exists, authentication immediately terminates with an error redirect to `/?error=authentication_failed`.
4. **User Provisioning:** Searches for an existing user where `provider = 'github'` and `provider_user_id = str(profile["id"])`. If not found, inserts a new user record.
5. **Session Creation:** Generates a 32-byte URL-safe cryptographic token, stores its SHA-256 hash in the `sessions` table (7-day lifetime), and issues the token in the session cookie.
6. **Redirect Destination:** Reads and removes `return_to` from the OAuth session (defaults to `"/"`).
7. **Frontend Redirect:** Redirects browser to `{FRONTEND_URL}{return_to}` with the session cookie attached.

### Success Response

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/dashboard
Set-Cookie: __Host-inoqr_session_id=kL9mX_2q8jP...; Max-Age=604800; Path=/; SameSite=strict; Secure; HttpOnly
```

### Failure Response

On state mismatch, OAuth error, or missing primary verified email:

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/?error=authentication_failed
```

On unhandled exceptions or GitHub API network errors:

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/?error=server_error
```

---

## 5. Get Current User

### `GET /api/v1/auth/me/`

Retrieves profile details for the currently authenticated user. Frontend applications should use this endpoint on page load to check authentication status.

### Authentication

Requires a valid `__Host-inoqr_session_id` session cookie.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `__Host-inoqr_session_id` | Cookie | `string` | Required | Plaintext 32-byte session token issued during OAuth callback. |

No request body or query parameters.

### Request

```http
GET /api/v1/auth/me/ HTTP/1.1
Host: api.inoqr.org
Cookie: __Host-inoqr_session_id=pA4q8jX_k9Lm...
```

### Success Response

**Status:** `200 OK`

```json
{
  "data": {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "image_url": "https://lh3.googleusercontent.com/a/...",
    "provider": "google"
  },
  "message": "User Found"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `data.name` | `string` | User display name from provider profile. |
| `data.email` | `string` | User email address. |
| `data.image_url` | `string` | User avatar image URL. |
| `data.provider` | `string` | Authentication provider used: `"google"` or `"github"`. |
| `message` | `string` | Fixed confirmation string: `"User Found"`. |

*Note: Database identifiers (`id`, `provider_user_id`) and timestamps are not exposed in the response.*

### Unauthenticated Responses

**Status:** `401 Unauthorized`

Occurs when no cookie is supplied:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "details": null
  }
}
```

Occurs when a cookie is supplied, but the session does not exist in the database or has expired (`expires_at <= current_timestamp`):

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid session",
    "details": null
  }
}
```

---

## 6. Logout

### `POST /api/v1/auth/logout/`

Terminates the user's active session, purges the database session record, deletes the browser session cookie, and redirects to the frontend homepage.

### Authentication

Reads the `__Host-inoqr_session_id` cookie if present. Missing or invalid cookies are handled gracefully without errors.

### Request

No request body.

```http
POST /api/v1/auth/logout/ HTTP/1.1
Host: api.inoqr.org
Cookie: __Host-inoqr_session_id=pA4q8jX_k9Lm...
```

### Execution Flow

1. Checks for the `__Host-inoqr_session_id` cookie.
2. If present, calculates its SHA-256 hash and executes `DELETE FROM sessions WHERE session_token_hash = :hash`.
3. If absent or invalid, silently continues (the operation is strictly idempotent).
4. Clears the cookie in the client browser with `Max-Age=0`.
5. Issues an HTTP `303 See Other` redirect to `{FRONTEND_URL}/`.

### Success Response

**Status:** `303 See Other`

```http
HTTP/1.1 303 See Other
Location: https://qr.inovuslabs.org/
Set-Cookie: __Host-inoqr_session_id=""; Max-Age=0; Path=/; ...
```

---

## 7. Delete Account

### `DELETE /api/v1/auth/account/`

Permanently deletes the currently authenticated user's account and all associated resources from the database, clears the session cookie, and redirects to the frontend homepage.

### Authentication

Requires a valid `__Host-inoqr_session_id` session cookie (`get_current_user`).

### Request

No request body.

```http
DELETE /api/v1/auth/account/ HTTP/1.1
Host: api.inoqr.org
Cookie: __Host-inoqr_session_id=pA4q8jX_k9Lm...
```

### Execution Flow

1. Validates the session cookie against the database. If invalid or missing, immediately returns `401 Unauthorized` JSON error.
2. Executes `DELETE FROM users WHERE id = :user_id`.
3. Due to foreign key `ON DELETE CASCADE` and ORM cascade rules, the following records belonging to the user are automatically and permanently deleted:
   - All active user sessions (`sessions`)
   - All user folders (`folders`)
   - All user QR codes (`qr_codes`)
4. Clears the `__Host-inoqr_session_id` cookie on the client (`Max-Age=0`).
5. Issues an HTTP `303 See Other` redirect to `{FRONTEND_URL}/`.

### Success Response

**Status:** `303 See Other`

```http
HTTP/1.1 303 See Other
Location: https://qr.inovuslabs.org/
Set-Cookie: __Host-inoqr_session_id=""; Max-Age=0; Path=/; ...
```

### Unauthenticated Response

**Status:** `401 Unauthorized`

If the request lacks a valid session cookie, account deletion is blocked:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "details": null
  }
}
```

*Note: Unlike successful deletion which redirects, unauthorized requests receive a standard JSON 401 response.*

---

## Return Destination (`return_to`)

The `return_to` query parameter enables the frontend to preserve the user's navigational context across external OAuth redirects.

### Specification

* **Accepted On:** `GET /api/v1/auth/login/google/` and `GET /api/v1/auth/login/github/`
* **Type:** `string`
* **Default:** `"/"`
* **Format:** Relative application path starting with a single forward slash (e.g., `"/create-qr"`, `"/folders/2a3b"`).

### Validation Logic

The backend enforces validation via `validate_return_to(return_to)`:

```python
def validate_return_to(return_to: str) -> str:
    if not return_to.startswith("/") or return_to.startswith("//"):
        return "/"
    return return_to
```

### Security & Fallback Rules

* **Must start with `/`:** Prevents absolute external URLs (e.g., `https://evil.com` or `javascript:...`).
* **Must not start with `//`:** Prevents protocol-relative open redirect attacks (e.g., `//evil.com`).
* **Safe Fallback:** If `return_to` is omitted, empty, or fails the validation rules, it is silently reset to `"/"`. It will never throw a `422 Unprocessable Entity` or abort login.
* **Storage Lifecycle:** The validated path is held in the encrypted temporary OAuth cookie during provider authorization and popped upon successful callback.
* **Error Behavior:** If OAuth fails, `return_to` is disregarded; the user is redirected to `{FRONTEND_URL}/?error=...`.

---

## Session Management & Cookie

InoQR uses server-managed sessions identified by an opaque, cryptographically random cookie.

### Cookie Attributes

| Attribute | Value | Rationale |
|-----------|-------|-----------|
| **Name** | `__Host-inoqr_session_id` | Uses the browser `__Host-` prefix standard. |
| **Value** | 32-byte URL-safe string | Cryptographically random token generated by `secrets.token_urlsafe(32)`. |
| **HttpOnly** | `True` | Inaccessible to client-side JavaScript (`document.cookie`), mitigating XSS token theft. |
| **Secure** | `True` | Transmitted exclusively over secure HTTPS connections. |
| **SameSite** | `strict` | Cookie is not sent on any cross-site requests, mitigating CSRF attacks. |
| **Path** | `/` | Valid across the entire application domain. |
| **Max-Age** | `604800` | 7 days in seconds (7 &times; 24 &times; 60 &times; 60). |

### The `__Host-` Cookie Prefix

The `__Host-` prefix triggers strict browser-level security checks:
1. Must be served with the `Secure` flag over HTTPS.
2. Must have `Path=/`.
3. Must not specify a `Domain` attribute (bound strictly to the host origin, preventing subdomain injection).

### Database Storage & Validation

* The server never stores the raw session token. It stores only the SHA-256 hash (`session_token_hash`).
* To validate a request, the backend computes the SHA-256 hash of the incoming cookie and searches for:
  ```sql
  SELECT * FROM sessions
  WHERE session_token_hash = :hash
    AND expires_at > CURRENT_TIMESTAMP;
  ```
* Sessions older than 7 days are considered invalid and are periodically purged by a background task.

### Frontend Guidelines for Session Handling

* **Do not attempt to read or modify the cookie:** JavaScript cannot access `HttpOnly` cookies.
* **Do not store tokens manually:** Never copy tokens to `localStorage` or `sessionStorage`.
* **Include credentials:** Every frontend API request made via `fetch` or `axios` must include credentials:
  - `fetch(url, { credentials: "include" })`
  - `axios.get(url, { withCredentials: true })`

---

## OAuth Providers Specification

The backend integrates two distinct OAuth providers with provider-specific identity retrieval logic:

### Provider Comparison

| Attribute | Google | GitHub |
|-----------|--------|--------|
| **Login Route** | `GET /api/v1/auth/login/google/` | `GET /api/v1/auth/login/github/` |
| **Callback Route** | `GET /api/v1/auth/google/callback/` | `GET /api/v1/auth/github/callback/` |
| **Protocol** | OAuth 2.0 / OpenID Connect | OAuth 2.0 |
| **Scopes Requested** | `openid email profile` | `user` |
| **PKCE Enabled** | Yes (`code_challenge_method="S256"`) | Yes (`code_challenge_method="S256"`) |
| **Auth Parameters** | Standard | `prompt="select_account"` |
| **Identity Source** | OIDC `userinfo` claims from ID Token | `GET https://api.github.com/user` |
| **Email Source** | `email` claim in OIDC `userinfo` | `GET https://api.github.com/user/emails` |
| **Email Requirement** | Handled by Google account | Primary & verified email **mandatory** |
| **Unique User Key** | `('google', profile['sub'])` | `('github', str(profile['id']))` |

### Account Partitioning

* Accounts are segregated by provider via composite unique constraints:
  - `uq_provider`: `(provider, provider_user_id)`
  - `uq_provider_email`: `(provider, email)`
* A user signing in with Google and a user signing in with GitHub are treated as separate accounts, even if both accounts share the same email address. Account linking is not supported.

---

## Error Handling & Response Schemas

Authentication-related errors fall into two distinct categories:

1. **OAuth Browser Redirect Errors:** Returned during the OAuth handshake.
2. **JSON API Errors:** Returned on standard API requests.

### 1. OAuth Redirect Errors

When an error occurs during OAuth authorization or callback handling, the backend redirects the user's browser to the frontend root URL with an `error` query parameter:

```text
GET {FRONTEND_URL}/?error={error_code}
```

| Error Code | HTTP Status | Trigger Condition | Frontend Recommended Action |
|------------|-------------|-------------------|-----------------------------|
| `authentication_failed` | `302 Found` | OAuth state mismatch (`MismatchingStateError`), rejected consent, provider exchange error, or missing verified primary email on GitHub. | Display: *"Authentication failed. Please try again."* |
| `server_error` | `302 Found` | Uncaught server exception, database error during callback, or network failure reaching provider APIs. | Display: *"Something went wrong on our server. Please try again later."* |

### 2. JSON API Errors

Direct API requests that fail return JSON adhering to the standardized `ErrorResponse` model.

#### Error Response Schema

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

* `error.code` (`string`): Machine-readable uppercase error identifier.
* `error.message` (`string`): Human-readable summary of the error.
* `error.details` (`object` or `null`): Parameter-level error details (used primarily in validation failures; `null` on other errors).

#### Common API Error Statuses

##### 401 Unauthorized

Returned when an authenticated route (`/me/`, `/account/`) is called without a valid session.

* **Missing session cookie:**
  ```json
  {
    "error": {
      "code": "UNAUTHORIZED",
      "message": "Authentication required",
      "details": null
    }
  }
  ```
* **Invalid or expired session:**
  ```json
  {
    "error": {
      "code": "UNAUTHORIZED",
      "message": "Invalid session",
      "details": null
    }
  }
  ```

##### 404 Not Found

Returned when accessing non-existent routes or URLs missing trailing slashes without redirect support.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Not Found",
    "details": null
  }
}
```

##### 405 Method Not Allowed

Returned when invoking an endpoint with an unsupported HTTP method (e.g., `GET /api/v1/auth/logout/`).

```json
{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "Method Not Allowed",
    "details": null
  }
}
```

##### 422 Unprocessable Entity

Returned if request validation fails. Note that authentication query parameters (like `return_to`) are permissive strings and sanitize silently; 422 is only encountered if invalid payloads are sent to future or malformed request parameters.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request Validation Failed",
    "details": {
      "parameter_name": "Field required"
    }
  }
}
```

##### 500 Internal Server Error

Returned when an unhandled server exception occurs during request processing.

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred",
    "details": null
  }
}
```