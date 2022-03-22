import json


def successful_login():
    return json.dumps(
        {
            "kind": "identitytoolkit#VerifyPasswordResponse",
            "localId": "4715c934-c2f1-4fd6-a1b7-1b5be21f7f55",
            "email": "john.doe@hummingbirdtech.com",
            "displayName": "John Doe",
            "idToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImIwNmExMTkxNThlOGIyODIxNzE0MThhNjdkZWE4Mzc0MGI1ZWU3N2UiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9zw6kgTC4gUGF0acOxbyIsInN0YWZmIjp0cnVlLCJyb2xlcyI6e30sImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9oYnQtc3RhZ2luZyIsImF1ZCI6ImhidC1zdGFnaW5nIiwiYXV0aF90aW1lIjoxNjQ3ODY0MTUyLCJ1c2VyX2lkIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1Iiwic3ViIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1IiwiaWF0IjoxNjQ3ODY0MTUyLCJleHAiOjE2NDc4Njc3NTIsImVtYWlsIjoiam9zZUBodW1taW5nYmlyZHRlY2guY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsiam9zZUBodW1taW5nYmlyZHRlY2guY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.jiQ7K8mr1uyBwoTcH2SXeOlEy4_PBkHjMaTrDx6rWI9pPWHdXZFeLzxsjP17LvmfIpEVRTnHCf8ygJ702UtPIB4P5bgFg4OYR8m2EsBtO5KPnz2pkHmhi30VN1j5hdXDPg5hoQOR5Z7Fp0uzoPUyReiKTPSm2njjikRnxm2gnARP-1H7PmmdsJ1hjQw0TuW7NWZefpJwpI25AjX3Gox846XjLBFn8apysu70FWpX2BcZwqUccD7QICMRAPRKps0bnOnplLMBuSK_mGYxp3V_gax1e02skGhOwoISb-QjhiC2eiTFLBuHGH9h63XZY5aeceGtx4iiwJhKGmqpb1cq_g",
            "registered": True,
            "refreshToken": "AIwUaOlT-NK9-hKTykqV84U3idvAvqzjobGIpr-EgiVleo54H1MSjcNGaEUF_zwJoUgH1_dzmf3QAmgqk-BhncroH5fri5gY817ym1yyhk20Yep0zANOhsRfMppRNJRwhn-QG5l9M41GsP4meHCSnm2yQSMXbMaSn17ER_i7lp34OV3wM1FN7Xs8NO9r0-6ruUu2M6pZxG14kfuTKod6V6tgzJ-PMY9NQsFPHCkdNCoepmWczhpMtPssVnEHaaptmftGMig77wDP",
            "expiresIn": "3600",
        }
    ).encode("utf-8")


def wrong_email():
    return json.dumps(
        {
            "error": {
                "code": 400,
                "message": "EMAIL_NOT_FOUND",
                "errors": [{"message": "EMAIL_NOT_FOUND", "domain": "global", "reason": "invalid"}],
            }
        }
    ).encode("utf-8")


def wrong_password():
    return json.dumps(
        {
            "error": {
                "code": 400,
                "message": "INVALID_PASSWORD",
                "errors": [
                    {"message": "INVALID_PASSWORD", "domain": "global", "reason": "invalid"}
                ],
            }
        }
    ).encode("utf-8")


def wrong_api_key():
    return json.dumps(
        {
            "error": {
                "code": 400,
                "message": "API key not valid. Please pass a valid API key.",
                "errors": [
                    {
                        "message": "API key not valid. Please pass a valid API key.",
                        "domain": "global",
                        "reason": "badRequest",
                    }
                ],
                "status": "INVALID_ARGUMENT",
                "details": [
                    {
                        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                        "reason": "API_KEY_INVALID",
                        "domain": "googleapis.com",
                        "metadata": {"service": "identitytoolkit.googleapis.com"},
                    }
                ],
            }
        }
    ).encode("utf-8")
