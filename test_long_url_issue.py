#!/usr/bin/env python3

"""
Test script to verify if long URLs cause LLM to return empty responses
"""

import json
from json_repair import repair_json

# Test with short URL
short_url = "https://example.com"
short_action = {
    "go_to_url": {
        "url": "PLACEHOLDER_URL"
    }
}

# Test with actual long presigned URL
long_url = "https://nhk8sx2goysqdri.studio.us-east-1.sagemaker.aws/auth?token=eyJhbGciOiJIUzI1NiJ9.eyJzcGFjZU5hbWUiOiJhZGFtLXNwYWNlLTE3NTIyNzkyOTMwNzYiLCJwYXJ0bmVyQXBwVXNlcklkZW50aXR5U291cmNlIjoiSWFtU2Vzc2lvbk5hbWUiLCJwYXJ0bmVyQXBwVXNlcklkZW50aXR5IjoiYm90b2NvcmUtc2Vzc2lvbi0xNzU0MDA0NDg1IiwiZmFzQ3JlZGVudGlhbHMiOiJBWUFEZU5DRGxFVmhObXFMZU5wa24yajE3bjBBWHdBQkFCVmhkM010WTNKNWNIUnZMWEIxWW14cFl5MXJaWGtBUkVGMmFUaFFRMkZ3WTB3eFRUZ3dSVTFUV1V0b1lWUTJVWGwzV2xrd2NpOUJZVXB4YkdKVVUyNDBSMWhKVnk5Q1RHRklVSFJyVVN0dmQzZ3hUVUpVTVZWdWR6MDlBQUVBQjJGM2N5MXJiWE1BUzJGeWJqcGhkM002YTIxek9uVnpMV1ZoYzNRdE1UbzVPREF6TlRJNE1qWXhNVFU2YTJWNUwyRTRPVGd5Wm1VNExURTNOemN0TkdJMFppMDRPVlU1TFdNMk5XTXhPV0l4WWpNeE1BQzRBUUlCQUhodjFjR3RRS3NsU2RUL000ZGQxdnhPU3dTRDQwUGZkWkphdUhqeFowTVVrd0ZTQStxTHk5WllEZ2E1S3Rqc1NwdFNBQUFBZmpCOEJna3Foa2lHOXcwQkJ3YWdiekJ0QWdFQU1HZ0dDU3FHU0liM0RRRUhBVEFlQmdsZ2hrZ0JaUU1FQVM0d0VRUU1nSWxFUTkxYnJacTJVOUpBQWdFUWdEdGFwSUhDaSt4blB6UzEyaWpEblJlTEZ3cUlZbXllVHdDaG1Yb05YakI3bHE2QnJTdFh3cjdSNWpFclJzcWd2YldxaElZWElhejBDN0U3OGdJQUFBQUFEQUFBRUFBQUFBQUFBQUFBQUFBQUFBRDNYWjNtL0FQOFIzNU4vb0orOGhqcS8vLy8vd0FBQUFFQUFBQUFBQUFBQUFBQUFBRUFBQVVqL00vbUxucG4zdEZybEJlRWpjNzZlMWYvTmtEQnFVWXM2U1BhNExFOHdmTWNDZThDQ2tuRmZ1NkIvVmgyWGw3WkVvOE82TGxyRzZEYUdvdlhVMmFlRi90K1I5Q2Z0U3JyTFBlL0wwT2swZnNJTzNna29qUEJTVDZmMSswZUlMOG1ucFlSMWN2dXU5VFJoZjJ0RDRJZXljRTJKSWlOZTUwNHFtSFh6RGhlNFRvVi9KQmxRMDNHejhFMHhKenVsUW9DSTdXWkxwTlE2dmFSWlV3SlBlQnpRa2NQYm0zN1hyZVFlMGlyMjQ0YkxMcHJBbWlpUEl6blBqanNLbHI4L3lPQTE2UEFHU3RVRWpZc2YvQmgvVEk5c0JWS1NSQWJRSG53Y01nU2ZFcnFPK0h1STUxcUk3MGNSYlMralJURGNSTzZDMmdiSC9pY2V6M1M2ckgrYUFlM1FvS0JSL2FGSGZFalBSd20yQ2tpZVZKOVROa2NvTzhVQ0xsU3hyamV2dEs5bkpRV1lDb2hvVDh5UWVyS05UZlJVeWI4RHlFR3ZHdUkvM0N2U2dOQ3B6RVgxVlpOeUIvRk9iK0MrSU1IalZKRlQ4TWdGRmdCeHI2aXBScENPL2tnMEVJdVlsZUIrWElFZ2krZk92MDU5Vyt4WFF2ZXB5a2N3NUJNVk1jSldsYzhzaDBRZm5XOVd1UFFaeFc3a0NzdXNLakEvZVpUQlFWQW1XV3FCaEFxeXZpUHRzQzcvR3lTWnRCY1FLZHF0eitlRmJpK0lWemszUmhVWHRPZVE0UndKb2FIdFd2emJJcEhya0ZhcEE4VTdGa0d0TUdQL1dZUVp2UXZ2S3djNFV5NGxyNHhyRWhsOS9ITjd2OVhoektvTEZEeFpVRDhqdVN1bHo3VTk4M1hzTFp5Q2RJMUdLMnltbjNSRW5rT0REb05BeFZ6aVA3dU1CZEI0YllCdVNNcEt3NEhyRWlLQWZiR3dwVU42UHJPdVBtZW9Bb1lmZkd2UHpqN1ZkaDFsc3NoZEhJcFdaU0xNdEMzbHlhUVVxbHgya0k1Y0FvUWx4Y2dwWVBsTlFvVmVTVGtyZThSdVFjdnJRWTFDN1RVdnhCcG4wZ0hVMXR6TUF1eUtuS3RpL1FYcU5wT0dKd2ZWbE1za0xGdkRvQ0tRNDdCcTlOblZKSExQVHFFK2hMT01tV1RIS3RJQ0QwZDExZ2JVajVqM1ZmSmpuU3l1UWc1ZEd5UHp1MWxmRW15cVRZTUVSQ3lwb09ldjhJa3hjL2xFeXYvWWJWdHc0cFp6aVdsbXR3RzNTNVgvakZnQjZhN0FMTGlkYUNQVkZWN3Fqd0txYTFTUjFPZndaY3ZoQXpaYjNPTk54VjVlNFRlZUFkM1dkOERkZkJWVHdFS3llMDFPWEpYTHc1aTFxZDJZOGhXSmFIV0d4YUJmSy9TZlpzakRFcnd2V052dlk1b2JLZ2tvSUl3akxHY2M4d3JCeGpEYlVZSGVTSWF2UUg0aG1sNFovTENWaXpOaFlLdkdMTGl0VVNuRERsdkFXcllwY1hyd1o0TUlTa2tQWTI1N0wyT2REM0Jtb0Q2K0pFQ2YzZkdKSmJTYyt5RlZweUFuS2ZEZ1VNbzN6VHVYNWFPOU1VUllJUE5JY21sZG51WVczK2psbGM4SnFsbC9RdnpocDUwVmsxM251STFBRXlPR0ZjelROVUJETVlWbXE2enlCUFpFRHI1Wk9iU0kzcXhtUnRpMFAvUmx5QXB5OUFxZ0g1N2wra1N1VTVPa1lzSDhvNERDbnN2RnhyVVQzeTVXQTFBdXc5eVV5MzZPcEI0UERIYVV3SnhVSVdOYWxhRkJKYmNjVUpudExLVE9MYWFEdGEyWUU2WXkrdUo0cURjZStQSGkrdGtuZ0pDOHMxekd6YUVoMk1FTi9RZkFTeGpxR3hIK29GYS90MFQ2Q1pscHJWd2lwSm1MbG8zRVVaTzFVYkhwY2ZsVEhyOW91SWZRNFpjZjRvTjdkelZUYm9xeGJDV2NtSmlmVGxaYkZZZ1JCZEpOWVFoNnhheFNyMHZjN3l6elIyVFVLOUs4MVJqcUhvSGdWSFpuTVVmQTJIbUxuTHI2ekZVYnhmVkR4TEhNSk9mUlpxTXVtbmpvVWNlS2dGRXQzU2h0VEpDbjh1NkZaUVoyY1pUdzI0SGNrUlgyVGZKSDVzSTRheUZCSUVkUElheDFtOVlRK2xjRk11a2hWczZGKzJlcjZzaUlRZW1CSWx0YU1Ecy9SbWZia2tmNE5oaEN0OUR4K0d1SHBQU3J0ekVWS0R0ZExvOGxJbW1rRkpFelB3Qkl6Qm5qb2tqVzl1YUprZm1JSVk3MC9wSzNyRXhNWFVBWnpCbEFqRUFtQWE2N1ZELzhaVnFMNkhmdm81eUpTUnRiYXBiT2JJZlVacW4xNzQ2a052SUFaWk9idUU1V1BWVStYbDc4NGFJQWpCYmZVb3ZacDZPOHV6NWV3QTNNRXZHV3hHakR0d2R6b0JkWTBUckg4NjlYL0VBTlRMSnZHZ3BlK2ZraWpJa2RBND0iLCJjaXBoZXJUZXh0IjoiQVFJQkFIaHYxY0d0UUtzbFNkVC9NNGRkMXZ4T1N3U0Q0MFBmZFpKYXVIanhaME1Va3dISFMxN1A1cWcvaW4vWnYvS0EwczJ4QUFBQW9qQ0Jud1lKS29aSWh2Y05BUWNHb0lHUk1JR09BZ0VBTUlHSUJna3Foa2lHOXcwQkJ3RXdIZ1lKWUlaSUFXVURCQUV1TUJFRURHUmI5UlZtdjVGOVVKWkFEUUlCRUlCYk8xcGhuN1ZQdzBySXpHRCtnRnV4N1ZTcWNxUGcwSEpTeTl2VXFiTHd3ZitnVjROMkJNN1pJd3F0dW56dnZDb3VzSW5GYlVLV2hkSmhJS3doS1JyWVpTeTZRK3B1ajRvcHVFb05qSU5LY2xiVWdIaGNtSjF4QWVOMHVBPT0iLCJpZGVudGl0eUlkIjoiYWRhbS1zcGFjZS0xNzUyMjc5MjkzMDc2IiwidXNlclByb2ZpbGVOYW1lIjoiYWRhbS10ZXN0LXVzZXItMTc1MjI3OTI4MjQ1MCIsImxhbmRpbmdVcmlTY2hlbWUiOiJhcHAiLCJsYW5kaW5nVXJpQXBwVHlwZSI6Ikp1cHl0ZXJMYWIiLCJsYW5kaW5nVXJpRGVlcExpbmsiOiIiLCJzdWIiOiJkLTljcGNod3oxbm5ubyIsImV4cCI6MTc1NDA0NzY4NiwiaWF0IjoxNzU0MDA0NDg2fQ.ID4lqmSG1qaxraHCfhnNpuJ0Ifv_ar3XOqnODVBxLlc"

long_action = {
    "go_to_url": {
        "url": "PLACEHOLDER_URL"
    }
}

def test_placeholder_replacement(action_dict, url, test_name):
    print(f"\n=== {test_name} ===")
    
    # Convert to JSON
    action_json = json.dumps(action_dict)
    print(f"Original JSON length: {len(action_json)}")
    
    # Replace placeholder
    modified_json = action_json.replace("PLACEHOLDER_URL", url)
    print(f"Modified JSON length: {len(modified_json)}")
    print(f"URL length: {len(url)}")
    
    # Try to parse back
    try:
        parsed = json.loads(modified_json)
        print("✅ JSON parsing successful")
        print(f"Parsed URL length: {len(parsed['go_to_url']['url'])}")
        return True
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing URL length impact on JSON processing...")
    
    # Test short URL
    short_success = test_placeholder_replacement(short_action, short_url, "SHORT URL TEST")
    
    # Test long URL
    long_success = test_placeholder_replacement(long_action, long_url, "LONG URL TEST")
    
    print(f"\n=== SUMMARY ===")
    print(f"Short URL test: {'✅ PASS' if short_success else '❌ FAIL'}")
    print(f"Long URL test: {'✅ PASS' if long_success else '❌ FAIL'}")
    
    if long_success:
        print("\n🔍 JSON processing works fine with long URLs.")
        print("🤔 The issue might be in LLM context window or token limits.")
    else:
        print("\n🚨 JSON processing fails with long URLs!")
        print("🔧 This confirms the root cause of the problem.")
