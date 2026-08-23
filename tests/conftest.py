from unittest.mock import Mock

import pytest

from game_vault.collectors.playstation_collector import PlayStationCollector


@pytest.fixture
def mock_psn_client() -> Mock:
    return Mock()


@pytest.fixture
def playstation_collector(mock_psn_client, tmp_path) -> PlayStationCollector:
    return PlayStationCollector(
        client=mock_psn_client,
        raw_dir=tmp_path,
    )


@pytest.fixture
def legacy_profile() -> dict:
    return {
        "profile": {
            "onlineId": "TestUser",
            "accountId": "123456789",
            "npId": "abcdefg1234567",
            "avatarUrls": [
                {"size": "l", "avatarUrl": "https://test-url.com/test_image.png"}
            ],
            "plus": 0,
            "aboutMe": "",
            "languagesUsed": ["en-GB"],
            "trophySummary": {
                "level": 250,
                "progress": 50,
                "earnedTrophies": {
                    "platinum": 1,
                    "gold": 21,
                    "silver": 192,
                    "bronze": 864,
                },
            },
            "isOfficiallyVerified": False,
            "personalDetail": {"firstName": "Test", "lastName": "User"},
            "personalDetailSharing": "no",
            "personalDetailSharingRequestMessageFlag": False,
            "primaryOnlineStatus": "offline",
            "presences": [
                {
                    "onlineStatus": "offline",
                    "hasBroadcastData": False,
                    "lastOnlineDate": "2026-08-24T21:14:18Z",
                }
            ],
            "friendRelation": "no",
            "requestMessageFlag": False,
            "blocking": False,
            "following": False,
            "consoleAvailability": {"availabilityStatus": "offline"},
        }
    }


@pytest.fixture
def devices() -> list[dict[str, str]]:
    return [
        {
            "deviceId": "asd156a1da61da3d24aw8c1a132da0w5d4a3",
            "deviceName": "My Test PS3 System",
            "deviceType": "PS3",
            "activationType": "PSN",
            "activationDate": "2015-02-28T12:51:42.702Z",
        },
        {
            "deviceId": "ca5s61ca65c1a32df1wa6d1as32c11re156rbsevr15",
            "deviceType": "PS4",
            "activationType": "PSN_GAME_V3",
            "activationDate": "2019-01-07T10:19:28.291Z",
            "accountDeviceVector": "/mt4io5yn9HS7j",
        },
        {
            "deviceId": "fe611c6a54bnvwae65r4b21fse65rc465r3ba24a5w0cawe",
            "deviceType": "PS5",
            "activationType": "PRIMARY",
            "activationDate": "2021-06-15T13:54:46.509Z",
            "accountDeviceVector": "1HTRH1V35fdfv126F21fe6",
        },
    ]


@pytest.fixture
def played_titles() -> list[dict]:
    return [
        {
            "title_id": "TEST12345_00",
            "name": "Test Game",
            "image_url": "https://test-url.com/test/f56e1df89d4D81EF4gf44e.png",
            "category": "unknown",
            "play_count": 154,
            "first_played_date_time": "2019-04-30T08:24:15.520000+00:00",
            "last_played_date_time": "2026-08-08T13:41:06.350000+00:00",
            "play_duration": 62856,
        },
        {
            "title_id": "TEST67890_00",
            "name": "Test Game 2",
            "image_url": "https://test-url.com/test/aqw56d165v1ras6c1qaw6da51asd.png",
            "category": "ps5_native_game",
            "play_count": 19,
            "first_played_date_time": "2026-07-10T13:47:24+00:00",
            "last_played_date_time": "2026-07-27T20:53:52.550000+00:00",
            "play_duration": 217164,
        },
        {
            "title_id": "TEST23456_00",
            "name": "Test Game 33",
            "image_url": "https://test-url.com/test/a65s1dx654RGH65AS4r6g1w4G64eaF45.png",
            "category": "ps5_native_game",
            "play_count": 117,
            "first_played_date_time": "2022-11-17T11:09:09+00:00",
            "last_played_date_time": "2026-02-02T23:18:42.350000+00:00",
            "play_duration": 439663,
        },
    ]


@pytest.fixture
def trophy_titles() -> list[dict]:
    return [
        {
            "np_service_name": "trophy2",
            "np_communication_id": "TEST12345_00",
            "trophy_set_version": "01.00",
            "title_name": "Test Game",
            "title_detail": None,
            "title_icon_url": "https://test-url.com/test_trophy/6168131-a15f-58b23-ca58df-65af1651fa.png",
            "title_platform": ["PS5"],
            "has_trophy_groups": None,
            "progress": 21,
            "hidden_flag": None,
            "earned_trophies": {"bronze": 28, "silver": 8, "gold": 1, "platinum": 0},
            "defined_trophies": {"bronze": 32, "silver": 20, "gold": 3, "platinum": 1},
            "last_updated_datetime": "2026-06-18T20:43:21+00:00",
            "np_title_id": None,
        }
    ]
