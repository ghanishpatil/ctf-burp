# 🌩️ Eleven’s Signal Station
**Category:** Web  
**Difficulty:** Hard (BurpSuite-focused)  
**Tech stack:** HTML (frontend) + Python (Flask backend)  
**Points:** 900  
**Type:** Shared instance (single-hosted). No per-user containers required.

---

## Story / Flavor
Beneath Hawkins Middle, a relay node replays psychic signals. Eleven built a filter to keep dangerous commands out, but the relay and the front-end disagree on how to interpret duplicate parameters. If you can craft raw requests (Burp required), you can confuse the relay into thinking you are a privileged operator — and Eleven will reveal a vision.

---

## Objective
Exploit parameter-handling differences between the reverse proxy (first-value-wins) and the backend (last-value-wins) to have the backend treat your request as coming from the privileged operator. Then GET:

GET /visions/eleven-only

kotlin
Copy code

The endpoint will return the final flag:

CSBC{ELEVEN_SIGNAL_STATION_<SECRET>}

markdown
Copy code

(Replace `<SECRET>` with your flag string when deploying.)

---

## What players receive
- `index.html` — the client page with the message form and a tiny client-side filter.
- `client.js` — (optional separate file) simple JS that blocks dangerous inputs (obfuscated/minified lightly).
- `server.py` — Flask backend that:
  - serves the page,
  - accepts `POST /api/send` (application/x-www-form-urlencoded),
  - parses `user` and `message` (last-value-wins),
  - sets a temporary request-level `isOperator` if backend sees `user == "operator"`,
  - serves `/visions/eleven-only` only when request-level `isOperator` is true,
  - includes rate-limiting and temporary lockouts.
- `Dockerfile` — to run the app easily.
- `README.txt` — short story hint (public).
- `notes_admin.md` — (admin-only) solution steps + deployment notes **(keep private)**.

> Admin: put the `flag` in server config or an env var and do NOT include it in any public file.

---

## Technical summary (author-facing)
- Frontend: blocks `operator`, duplicate parameters and some special characters. This tempts players to bypass client-side validation using a proxy.
- Reverse proxy (simulated by a provided Nginx config or comment) is assumed to use first-value-wins semantics.
- Backend (Flask) parses `application/x-www-form-urlencoded` and results in *last-value-wins* semantics.
- The mismatch is the vulnerability: sending duplicate `user` parameters in an order that results in the backend seeing `operator` allows privilege escalation for that request.
- Brute-force and automation are deterred by:
  - simple session-level rate limiting (e.g., 5 failed elevation attempts → 30s lock),
  - server-side logging and detection of repeated identical requests,
  - client-side filtering that hides trivial approaches and forces proxy use.

---

## Player playbook (high-level, non-spoiler)
1. Open the page and submit a message. Note the client-side filter that forbids `user=operator`.  
2. Intercept the `POST /api/send` request with Burp Proxy.  
3. Craft a new raw POST body with **duplicate `user` parameters** in different orders (e.g., `user=guest&user=operator` or `user=operator&user=guest`). Test both.  
4. Use Burp Repeater to try different sequences and observe responses and headers. Watch for when the server returns any sign of elevated access or for `/visions/eleven-only` to produce content.  
5. Once the backend accepts you as operator for a request, fetch `/visions/eleven-only` to get the flag.

---

## Hints (laddered; reveal progressively)
- **Hint 1:** The UI tries to help — but it isn’t the final authority.  
- **Hint 2:** Send duplicates. Different systems choose different duplicates.  
- **Hint 3:** Try reordering parameters in the raw body (Burp Repeater). The proxy and backend disagree.  
- **Hint 4:** If brute-forcing, slow down — the station locks you briefly.

---

## Anti-abuse / Bruteforce protections (implementation notes)
- Implement a minimal per-IP request counter with short lockouts after N failed elevation attempts. (This is sufficient for a shared single-host CTF.)
- Log attempts for admin review.  
- Optionally serve a small “rate-limited” page if the IP is locked.

---

## Admin Solution — (KEEP PRIVATE)
> **Do not publish this section.** Use it only to verify solves or to generate hints if requested.

1. Browse to `/` and submit any message so the legitimate form request is generated. Capture the outbound `POST /api/send` using Burp Proxy (or any interceptor).  
2. Move the captured request into Burp Repeater. Delete everything after the headers except the `application/x-www-form-urlencoded` body so you can edit freely.  
3. Craft a payload that places a safe-looking value first and `operator` last, e.g.  
   `user=guest&user=operator&message=HelloFromTheVoid`  
   The reverse proxy will cache/route on the first key-value pair (treating `guest` as authoritative) while Flask keeps only the **last** entry for each repeated key during parsing, so the backend receives `user=operator`.  
4. Send the modified request repeatedly until you receive `{"status":"ok","privileged":true}` (the limiter allows four misses before locking for 30 seconds). If you get locked, wait for the cooldown or switch IP.  
5. Immediately issue `GET /visions/eleven-only` reusing the same session cookies. Because `g.is_operator` was set for that request lifecycle, the endpoint returns `{ "vision": "CSBC{ELEVEN_SIGNAL_STATION_<SECRET>}" }`.  
6. Variations that also work if a WAF normalizes parameters:  
   - `user=guest%20&user=operator&message=...` (encoded noise in the first value)  
   - `user=guest&message=test&user=operator` (space the privileged key away from the start)  
   - Mixed content types allowed by Burp (e.g., URL-encoded body with duplicated keys introduced via manual editor).  
7. Reminder: the privilege flag is request-scoped; you must fetch `/visions/eleven-only` right after a successful elevation attempt.