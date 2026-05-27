# Per-database configuration: versions, years, systems, satellite accounts
# (with GWP factors used to aggregate to a single "GHG" indicator) and the
# electricity sector/commodity labels to keep in the final emission factors.

properties = {
    'exiobase_monetary_iot': {
        'name': 'EXIOBASE',
        'table': 'IOT',
        'versions': [
            # '3.10.2',
            '3.10.1',
            ],
        'systems': ['ixi', 'pxp'],
        'years': range(1995,2025),
    },

    'eora26': {
        'name': 'EORA26',
        'table': 'IOT',
        'versions': ['199.82'],         # autodetected by mario.parse_eora
        'years': range(2000,2018),
    },

    'figaro': {
        'name': 'FIGARO',
        'table': 'IOT',
        'versions': ['v2025'],         
        'years': range(2010,2023),
    },

    'oecd-icio': {
        'name': 'OECD-ICIO',
        'table': 'IOT',
        'versions': ['v2025'],         
        'years': range(1995,2023),
    },

    'adb': {
        'name': 'ADB',
        'table': 'IOT',
        'versions': ['62 economies'],         
        'years': range(2007,2025),
    },

    'emerging': {
        'name': 'EMERGING',
        'table': 'IOT',
        'versions': ['2.2'],
        'years': [2015, 2018, 2021, 2023],
    },

    'gloria': {
        'name': 'GLORIA',
        'table': 'SUT',
        'versions': ['0.60'],
        'years': range(2013, 2021),
    },

}
