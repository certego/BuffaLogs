from impossible_travel.models import Config, Login, User


class Setup:
    def setup(self):
        user = User.objects.bulk_create(
            [
                User(username="Lorena Goldoni"),
                User(username="Asa Strickland"),
                User(username="Aisha Delgado"),
            ]
        )
        logins = Login.objects.bulk_create(
            [
                # Login for not vip_users but allowed_countries
                Login(
                    user=user[0],
                    timestamp="2023-03-08T17:08:33.358Z",
                    latitude=44.4937,
                    longitude=24.3456,
                    country="Italy",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36",
                ),
                Login(
                    user=user[0],
                    timestamp="2023-03-08T17:25:33.358Z",
                    latitude=45.4758,
                    longitude=9.2275,
                    country="Italy",
                    user_agent="Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5",
                ),
                # Login for vip_users but not allowed_countries
                Login(
                    user=user[1],
                    timestamp="2023-03-08T17:10:11.000Z",
                    latitude=22.3270,
                    longitude=82.6686,
                    country="India",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
                ),
                # Login for vip_users and allowed_countries
                Login(
                    user=user[1],
                    timestamp="2023-03-08T17:15:12.123Z",
                    latitude=44.4937,
                    longitude=24.3456,
                    country="Italy",
                    user_agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                ),
            ]
        )
        Config.objects.create(
            id=1,
            ignored_users=["N/A", "Not Available"],
            ignored_ips=["0.0.0.0", "192.168.1.0/24"],
            allowed_countries=["Italy", "Romania"],
            vip_users=["Asa Strickland", "Krista Moran"],
        )
