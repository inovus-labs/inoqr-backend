# QR Code Resolver API Documentation

## Base Path

```text
/r/{slug}/
```

The Resolver is the public-facing redirection engine of InoQR. It maps short, high-density QR code slugs to their configured destination URLs and issues immediate HTTP redirects to clients, mobile devices, and camera scanners.


---

## 1. Resolve QR Code

### `GET /r/{slug}/`

Resolves a QR code slug and redirects the client to the configured destination URL.

### Authentication

**Public / None.**

The endpoint is accessible without authentication cookies or bearer tokens so that any person, camera app, or barcode scanner can immediately resolve links.

### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `slug` | Path     | `string` | Required | Unique alphanumeric slug assigned to the dynamic QR code (maximum 25 characters). |

### Execution Flow


1. Receives the incoming `GET` request with path parameter `slug`.
2. Resolves an asynchronous database session via the `get_db` FastAPI dependency.
3. Executes an asynchronous query against the `qr_codes` table:

   ```python
   stmt = select(QrCode.destination).where(QrCode.slug == slug)
   ```
4. Evaluates query result:
   * **Slug Found:** Issues an HTTP `302 Found` response redirecting the client to the destination URL.
   * **Slug Not Found (**`**None**`**):** Calls `redirect_to_frontend("/?error=qr_not_found", status_code=302)`, sending the user to the frontend application error landing page.


---

### Request

```http
GET /r/inovus-launch/ HTTP/1.1
Host: api.inoqr.org
User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
```


---

### Responses

#### 1. Success Response (Redirect to Destination)

When the slug is valid and an active destination is mapped:

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://inovuslabs.org/events/launch-2026
Content-Length: 0
```

#### 2. Not Found Response (Redirect to Frontend)

When the slug does not exist in the database or has been deleted:

**Status:** `302 Found`

```http
HTTP/1.1 302 Found
Location: https://qr.inovuslabs.org/?error=qr_not_found
Content-Length: 0
```

#### 3. Unhandled Server Error

If a database connectivity issue or unexpected runtime error occurs, the global exception handler returns a standardized JSON error:

**Status:** `500 Internal Server Error`

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred",
    "details": null
  }
}
```


---

## Error Codes & Handling

### Frontend Redirect Query Parameters

When redirection fails due to an invalid slug, the client is redirected to the frontend root URL with an `error` query parameter:

```text
GET {FRONTEND_URL}/?error=qr_not_found
```

| Query Parameter | Trigger Condition | Recommended Frontend UI Behavior |
|-----------------|-------------------|----------------------------------|
| `?error=qr_not_found` | The requested slug does not match any record in `qr_codes`. | Display a notification or friendly modal: *"The QR code you scanned does not exist or has been disabled."* |


---

## Routing & Trailing Slashes

The endpoint route is defined with a trailing slash:

```python
@router.get("/r/{slug}/")
```

* **Standard Request:** `GET /r/my-code/` resolves directly with `302 Found`.
* **Missing Trailing Slash:** If a client requests `GET /r/my-code`, FastAPI/Starlette's default routing behavior issues a `307 Temporary Redirect` to `/r/my-code/` before processing the resolution query.


---

