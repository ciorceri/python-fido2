# Copyright (c) 2018 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Example demo server to use a supported web browser to call the WebAuthn APIs
to register and use a credential.

See the file README.adoc in this directory for details.

Navigate to https://localhost:5000 in a supported web browser.
"""
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity
from fido2.server import Fido2Server
from flask import Flask, session, request, redirect, abort, jsonify

import os
import fido2.features

fido2.features.webauthn_json_mapping.enabled = True


app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)  # Used for session.

# rp = PublicKeyCredentialRpEntity(name="Demo server", id="localhost")
rp = PublicKeyCredentialRpEntity(name="Demo server", id="fido.server")
server = Fido2Server(rp)


# Registered credentials are stored globally, in memory only. Single user
# support, state is lost when the server terminates.
credentials = []


@app.route("/")
def index():
    return redirect("/index.html")


@app.route("/api/register/begin", methods=["POST"])
def register_begin():

    try:
        auth_type = request.json['authenticator']
    except:
        auth_type = 'any'

    if auth_type == 'any':
        _authenticator_attachment = ['cross-platform', 'platform']
    else:
        _authenticator_attachment = auth_type

    options, state = server.register_begin(
        PublicKeyCredentialUserEntity(
            id=b"user_id",
            name="a_user",
            display_name="A. User",
        ),
        credentials,
        user_verification="discouraged",  # discouraged, preferred, required
        authenticator_attachment=_authenticator_attachment,
    )

    session["state"] = state
    print("\n\n\n\n")
    print(options)
    print("\n\n\n\n")


    return jsonify(dict(options))


@app.route("/api/register/complete", methods=["POST"])
def register_complete():
    response = request.json
    print("RegistrationResponse:", response)
    auth_data = server.register_complete(session["state"], response)

    credentials.append(auth_data.credential_data)
    print("REGISTERED CREDENTIAL:", auth_data.credential_data)
    return jsonify({"status": "OK"})


@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
    if not credentials:
        abort(404)

    options, state = server.authenticate_begin(credentials)
    session["state"] = state

    return jsonify(dict(options))


@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
    if not credentials:
        abort(404)

    response = request.json
    print("AuthenticationResponse:", response)
    server.authenticate_complete(
        session.pop("state"),
        credentials,
        response,
    )
    print("ASSERTION OK")
    return jsonify({"status": "OK"})


def main():
    print(__doc__)
    app.run(host='0.0.0.0', ssl_context="adhoc", debug=False)
    # use a selfsigned certificate (valid until 2033) : https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
    # app.run(host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'), debug=False)


if __name__ == "__main__":
    main()
