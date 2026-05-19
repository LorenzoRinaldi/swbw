# Per-database configuration: versions, years, systems, satellite accounts
# (with GWP factors used to aggregate to a single "GHG" indicator) and the
# electricity sector/commodity labels to keep in the final emission factors.

properties = {
    'exiobase_monetary_iot': {
        'name': 'EXIOBASE',
        'table': 'IOT',
        'versions': ['3.10.1', '3.9.6', '3.9.5', '3.8.2'],
        'systems': ['ixi', 'pxp'],
        'years': [2022, 2017],
        'gwps': {
            'CO2 - combustion - air': 1.0,
            'CH4 - combustion - air': 29.7,
            'N2O - combustion - air': 264.8,
            'HFC - air': 1,
            'SF6 - air': 23506,
            'CO - combustion - air': 4.1,
        },
        'labels_list': {
            'ixi': [
                'Production of electricity by coal',
                'Production of electricity by gas',
                'Production of electricity by nuclear',
                'Production of electricity by hydro',
                'Production of electricity by wind',
                'Production of electricity by petroleum and other oil derivatives',
                'Production of electricity by biomass and waste',
                'Production of electricity by solar photovoltaic',
                'Production of electricity by solar thermal',
                'Production of electricity by tide, wave, ocean',
                'Production of electricity by Geothermal',
                'Production of electricity nec',
            ],
            'pxp': [
                'Electricity by coal',
                'Electricity by gas',
                'Electricity by nuclear',
                'Electricity by hydro',
                'Electricity by wind',
                'Electricity by petroleum and other oil derivatives',
                'Electricity by biomass and waste',
                'Electricity by solar photovoltaic',
                'Electricity by solar thermal',
                'Electricity by tide, wave, ocean',
                'Electricity by Geothermal',
            ],
        },
    },

    'eora26': {
        'name': 'EORA26',
        'table': 'IOT',
        'versions': ['199.82'],         # autodetected by mario.parse_eora
        'years': [2017],
        'gwps': {
            # EORA26 satellite labels for the main GHGs (already CO2eq for some
            # rows but kept explicit here for transparency).
            'CO2': 1.0,
            'CH4': 29.7,
            'N2O': 264.8,
        },
        'labels_list': [
            'Electricity, Gas and Water',
        ],
    },

    'emerging': {
        'name': 'EMERGING',
        'table': 'IOT',
        'versions': ['2.2'],
        'years': [2023],
        'gwps': {
            'Coal': 1,
            'Natural gas': 1,
            'Oil products': 1,
            'Crude, NGL, Ref Feeds.': 1,
            'Oil shale & oil sands': 1,
            'Peat & Peat products': 1,
            'Other': 1,
        },
        'labels_list': ['Electricity'],
    },

    'gloria': {
        'name': 'GLORIA',
        'table': 'SUT',
        'versions': ['0.60'],
        'years': [2017, 2023],
        'gwps': {
            "Emissions (EDGAR) | 'co2_excl_short_cycle_org_c_total_EDGAR_consistent'": 1,
            "Emissions (EDGAR) | 'ch4_total_EDGAR_consistent'": 29.7,
            "Emissions (EDGAR) | 'n2o_total_EDGAR_consistent'": 264.8,
            "Emissions (EDGAR) | 'hfc_23_total_EDGAR_consistent'": 1,
            "Emissions (EDGAR) | 'sf6_total_EDGAR_consistent'": 23506,
            "Emissions (EDGAR) | 'co_total_EDGAR_consistent'": 4.1,
        },
        'labels_list': {
            'Commodity': ['Electric power generation, transmission and distribution'],
            'Activity': ['Electric power generation, transmission and distribution'],
        },
    },
}
