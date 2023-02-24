import calendar
import json
from datetime import date, datetime, timedelta

import pygal
from dateutil.relativedelta import relativedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from impossible_travel.models import Alert, Login, User
from impossible_travel.modules import impossible_travel
from pygal.style import Style

imp_travel = impossible_travel.Impossible_Travel()


def users_pie_chart(start, end):
    custom_style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#dee2e6",
        foreground_strong="#dee2e6",
        foreground_subtle="#dee2e6",
        transition="400ms ease-in",
        opacity="0.7",
        opacity_hover="0.9",
        colors=("#3174b0", "#8753de", "#f59c1a", "#ff3333"),
        value_colors=("#fff"),
        legend_font_size=25,
        tooltip_font_size=25,
    )
    users_pie_chart = pygal.Pie(style=custom_style, width=1000, height=750)

    users_pie_chart.add("No risk", User.objects.filter(updated__range=(start, end), risk_score="No risk").count())
    users_pie_chart.add("Low", User.objects.filter(updated__range=(start, end), risk_score="Low").count())
    users_pie_chart.add("Medium", User.objects.filter(updated__range=(start, end), risk_score="Medium").count())
    users_pie_chart.add("High", User.objects.filter(updated__range=(start, end), risk_score="High").count())
    return users_pie_chart.render(disable_xml_declaration=True)


def alerts_line_chart(start, end):
    custom_style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#dee2e6",
        foreground_strong="#dee2e6",
        foreground_subtle="#dee2e6",
        opacity=".7",
        opacity_hover=".9",
        transition="400ms ease-in",
        colors=("#3174b0", "#408fa8"),
        tooltip_font_size=20,
        x_labels_font_size=20,
    )
    alerts_line_chart = pygal.StackedBar(fill=True, show_legend=False, style=custom_style, width=1200, height=550, x_label_rotation=20)
    date_range = []
    alerts_in_range = []
    date_str = []
    delta_timestamp = end - start
    if delta_timestamp.days < 1:
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%H:%M:%S"))
            start = start + timedelta(minutes=59, seconds=59)
            date_range.append(start)
            start = start + timedelta(seconds=1)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                ).count()
            )
    elif delta_timestamp.days >= 1 and delta_timestamp.days <= 31:
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%Y-%m-%d"))
            start = start + timedelta(hours=23, minutes=59, seconds=59)
            date_range.append(start)
            start = start + timedelta(seconds=1)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                ).count()
            )
    else:
        start = timezone.datetime(start.year, start.month, 1)
        end = end.replace(tzinfo=None)
        while start <= end:
            date_range.append(start)
            date_str.append(start.strftime("%B %Y"))
            start = start + relativedelta(months=1)
            date_range.append(start)
        for i in range(0, len(date_range) - 2, 2):
            alerts_in_range.append(
                Alert.objects.filter(
                    login_raw_data__timestamp__range=(date_range[i].strftime("%Y-%m-%dT%H:%M:%S.%fZ"), date_range[i + 1].strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                ).count()
            )
    alerts_line_chart.x_labels = map(str, date_str)
    alerts_line_chart.add("", alerts_in_range)
    return alerts_line_chart.render(disable_xml_declaration=True)


def world_map_chart(start, end):
    custom_style = Style(
        background="transparent",
        plot_background="transparent",
        foreground="#dee2e6",
        foreground_strong="#dee2e6",
        foreground_subtle="#dee2e6",
        opacity=".7",
        opacity_hover=".9",
        transition="400ms ease-in",
        colors=("#3174b0", "#00acac", "#408fa8"),
        value_font_size=1,
        tooltip_font_size=2.5,
        major_label_font_size=1,
        label_font_size=1,
        value_label_font_size=4,
    )
    world_map_chart = pygal.maps.world.World(
        style=custom_style,
        width=380,
        height=160,
        show_legend=False,
    )
    countries = {
        "ad": "Andorra",
        "ae": "United Arab Emirates",
        "af": "Afghanistan",
        "al": "Albania",
        "am": "Armenia",
        "ao": "Angola",
        "aq": "Antarctica",
        "ar": "Argentina",
        "at": "Austria",
        "au": "Australia",
        "az": "Azerbaijan",
        "ba": "Bosnia and Herzegovina",
        "bd": "Bangladesh",
        "be": "Belgium",
        "bf": "Burkina Faso",
        "bg": "Bulgaria",
        "bh": "Bahrain",
        "bi": "Burundi",
        "bj": "Benin",
        "bn": "Brunei Darussalam",
        "bo": "Bolivia, Plurinational State of",
        "br": "Brazil",
        "bt": "Bhutan",
        "bw": "Botswana",
        "by": "Belarus",
        "bz": "Belize",
        "ca": "Canada",
        "cd": "Congo, the Democratic Republic of the",
        "cf": "Central African Republic",
        "cg": "Congo",
        "ch": "Switzerland",
        "ci": "Cote d'Ivoire",
        "cl": "Chile",
        "cm": "Cameroon",
        "cn": "China",
        "co": "Colombia",
        "cr": "Costa Rica",
        "cu": "Cuba",
        "cv": "Cape Verde",
        "cy": "Cyprus",
        "cz": "Czech Republic",
        "de": "Germany",
        "dj": "Djibouti",
        "dk": "Denmark",
        "do": "Dominican Republic",
        "dz": "Algeria",
        "ec": "Ecuador",
        "ee": "Estonia",
        "eg": "Egypt",
        "eh": "Western Sahara",
        "er": "Eritrea",
        "es": "Spain",
        "et": "Ethiopia",
        "fi": "Finland",
        "fr": "France",
        "ga": "Gabon",
        "gb": "United Kingdom",
        "ge": "Georgia",
        "gf": "French Guiana",
        "gh": "Ghana",
        "gl": "Greenland",
        "gm": "Gambia",
        "gn": "Guinea",
        "gq": "Equatorial Guinea",
        "gr": "Greece",
        "gt": "Guatemala",
        "gu": "Guam",
        "gw": "Guinea-Bissau",
        "gy": "Guyana",
        "hk": "Hong Kong",
        "hn": "Honduras",
        "hr": "Croatia",
        "ht": "Haiti",
        "hu": "Hungary",
        "id": "Indonesia",
        "ie": "Ireland",
        "il": "Israel",
        "in": "India",
        "iq": "Iraq",
        "ir": "Iran, Islamic Republic of",
        "is": "Iceland",
        "it": "Italy",
        "jm": "Jamaica",
        "jo": "Jordan",
        "jp": "Japan",
        "ke": "Kenya",
        "kg": "Kyrgyzstan",
        "kh": "Cambodia",
        "kp": "Korea, Democratic People's Republic of",
        "kr": "Korea, Republic of",
        "kw": "Kuwait",
        "kz": "Kazakhstan",
        "la": "Lao People's Democratic Republic",
        "lb": "Lebanon",
        "li": "Liechtenstein",
        "lk": "Sri Lanka",
        "lr": "Liberia",
        "ls": "Lesotho",
        "lt": "Lithuania",
        "lu": "Luxembourg",
        "lv": "Latvia",
        "ly": "Libyan Arab Jamahiriya",
        "ma": "Morocco",
        "mc": "Monaco",
        "md": "Moldova, Republic of",
        "me": "Montenegro",
        "mg": "Madagascar",
        "mk": "Macedonia, the former Yugoslav Republic of",
        "ml": "Mali",
        "mm": "Myanmar",
        "mn": "Mongolia",
        "mo": "Macao",
        "mr": "Mauritania",
        "mt": "Malta",
        "mu": "Mauritius",
        "mv": "Maldives",
        "mw": "Malawi",
        "mx": "Mexico",
        "my": "Malaysia",
        "mz": "Mozambique",
        "na": "Namibia",
        "ne": "Niger",
        "ng": "Nigeria",
        "ni": "Nicaragua",
        "nl": "Netherlands",
        "no": "Norway",
        "np": "Nepal",
        "nz": "New Zealand",
        "om": "Oman",
        "pa": "Panama",
        "pe": "Peru",
        "pg": "Papua New Guinea",
        "ph": "Philippines",
        "pk": "Pakistan",
        "pl": "Poland",
        "pr": "Puerto Rico",
        "ps": "Palestine, State of",
        "pt": "Portugal",
        "py": "Paraguay",
        "re": "Reunion",
        "ro": "Romania",
        "rs": "Serbia",
        "ru": "Russian Federation",
        "rw": "Rwanda",
        "sa": "Saudi Arabia",
        "sc": "Seychelles",
        "sd": "Sudan",
        "se": "Sweden",
        "sg": "Singapore",
        "sh": "Saint Helena, Ascension and Tristan da Cunha",
        "si": "Slovenia",
        "sk": "Slovakia",
        "sl": "Sierra Leone",
        "sm": "San Marino",
        "sn": "Senegal",
        "so": "Somalia",
        "sr": "Suriname",
        "st": "Sao Tome and Principe",
        "sv": "El Salvador",
        "sy": "Syrian Arab Republic",
        "sz": "Swaziland",
        "td": "Chad",
        "tg": "Togo",
        "th": "Thailand",
        "tj": "Tajikistan",
        "tl": "Timor-Leste",
        "tm": "Turkmenistan",
        "tn": "Tunisia",
        "tr": "Turkey",
        "tw": "Taiwan (Republic of China)",
        "tz": "Tanzania, United Republic of",
        "ua": "Ukraine",
        "ug": "Uganda",
        "us": "United States",
        "uy": "Uruguay",
        "uz": "Uzbekistan",
        "va": "Holy See (Vatican City State)",
        "ve": "Venezuela, Bolivarian Republic of",
        "vn": "Viet Nam",
        "ye": "Yemen",
        "yt": "Mayotte",
        "za": "South Africa",
        "zm": "Zambia",
        "zw": "Zimbabwe",
    }
    tmp = {}
    for key, value in countries.items():
        country_alerts = Alert.objects.filter(
            login_raw_data__timestamp__range=(start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")), login_raw_data__country=value
        ).count()
        if country_alerts == 0:
            tmp[key] = None
        else:
            tmp[key] = country_alerts
    world_map_chart.add("Alerts", tmp)
    return world_map_chart.render_data_uri()
