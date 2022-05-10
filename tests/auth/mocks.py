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


def successful_refresh_token():
    return {
        "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImJlYmYxMDBlYWRkYTMzMmVjOGZlYTU3ZjliNWJjM2E2YWIyOWY1NTUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9zw6kgTC4gUGF0acOxbyIsInN0YWZmIjp0cnVlLCJyb2xlcyI6e30sImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9oYnQtc3RhZ2luZyIsImF1ZCI6ImhidC1zdGFnaW5nIiwiYXV0aF90aW1lIjoxNjUyMTExMzEzLCJ1c2VyX2lkIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1Iiwic3ViIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1IiwiaWF0IjoxNjUyMTczMjk1LCJleHAiOjE2NTIxNzY4OTUsImVtYWlsIjoiam9zZUBodW1taW5nYmlyZHRlY2guY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsiam9zZUBodW1taW5nYmlyZHRlY2guY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.RvEu_zai4PVdRbD93G9z3zIERB-Z-TUAAxBuEqMLAwDjITQdYxs673kOJ70XM0syr1D92_KQ3gsGl1fI6iFlVMCHAP0YF_YaVSBIDvlyHIWbzqVHXn5jzwjsrupH53QnBT7LZDNiKvFNgW8d7GIHq0OyKUVQQG8vmEzjqTtqAV4MIKnH6JatthxnPuGdVh7twfmu5pJYS08Z8hRgm1eUOJfASEsdGPQn7O8WWC8VM4Y4lGYi3N6QQXUiHKNMZf0cDWnVxVxKFDG54NWtCDupvD6k3U85ZxgfQjrc4EAYu1JNmY2_oPYtSAuUNT8UhJFoySBx1_myZjNOKAuG-JE4oA",
        "expires_in": "3600",
        "token_type": "Bearer",
        "refresh_token": "AIwUaOmXReh98IRp91r5v2aJyOPMzgu4OC-v4EJSUX7v7sEC3qWznqsgTC68Ldy_6OPdR_x12H3cioy7OaW2nEycR1N45N63HLZLueUivPh3Hcpy1kZP0-Nr6ww8vaOX06JitcMc_sp6ObsiEf_Wfn0cWvNA4n-uwjdbMtr4FmI0scYxgDhN2n05gKbViJNLpikguxeVDsVei8Erdz-78iYjiHVDOTtnyC2cqpma4VSylGLpOvqIjzQnIUcxOaq7gHu6KrNVvlVN",
        "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImJlYmYxMDBlYWRkYTMzMmVjOGZlYTU3ZjliNWJjM2E2YWIyOWY1NTUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9zw6kgTC4gUGF0acOxbyIsInN0YWZmIjp0cnVlLCJyb2xlcyI6e30sImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9oYnQtc3RhZ2luZyIsImF1ZCI6ImhidC1zdGFnaW5nIiwiYXV0aF90aW1lIjoxNjUyMTExMzEzLCJ1c2VyX2lkIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1Iiwic3ViIjoiNDcxNWM5MzQtYzJmMS00ZmQ2LWExYjctMWI1YmUyMWY3ZjU1IiwiaWF0IjoxNjUyMTczMjk1LCJleHAiOjE2NTIxNzY4OTUsImVtYWlsIjoiam9zZUBodW1taW5nYmlyZHRlY2guY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsiam9zZUBodW1taW5nYmlyZHRlY2guY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.RvEu_zai4PVdRbD93G9z3zIERB-Z-TUAAxBuEqMLAwDjITQdYxs673kOJ70XM0syr1D92_KQ3gsGl1fI6iFlVMCHAP0YF_YaVSBIDvlyHIWbzqVHXn5jzwjsrupH53QnBT7LZDNiKvFNgW8d7GIHq0OyKUVQQG8vmEzjqTtqAV4MIKnH6JatthxnPuGdVh7twfmu5pJYS08Z8hRgm1eUOJfASEsdGPQn7O8WWC8VM4Y4lGYi3N6QQXUiHKNMZf0cDWnVxVxKFDG54NWtCDupvD6k3U85ZxgfQjrc4EAYu1JNmY2_oPYtSAuUNT8UhJFoySBx1_myZjNOKAuG-JE4oA",
        "user_id": "4715c934-c2f1-4fd6-a1b7-1b5be21f7f55",
        "project_id": "859455874565",
    }


def invalid_refresh_token():
    return {
        "error": {"code": 400, "message": "INVALID_REFRESH_TOKEN", "status": "INVALID_ARGUMENT"}
    }


def expired_refresh_token():
    return {"error": {"code": 400, "message": "TOKEN_EXPIRED", "status": "INVALID_ARGUMENT"}}


def refresh_token_user_disabled():
    return {"error": {"code": 400, "message": "USER_DISABLED", "status": "INVALID_ARGUMENT"}}


def refresh_token_user_deleted():
    return {"error": {"code": 400, "message": "USER_NOT_FOUND", "status": "INVALID_ARGUMENT"}}
