"""Place suggestions used when no Google Places key is configured.

Cities and towns from every division, plus busy areas in the biggest cities. Add your own:
anything typed into the field is accepted, this list only speeds typing up.
"""

DHAKA_AREAS = [
    "Mirpur 1", "Mirpur 10", "Mirpur 12", "Pallabi", "Shewrapara", "Agargaon", "Farmgate",
    "Tejgaon", "Mohakhali", "Banani", "Gulshan 2", "Badda", "Rampura", "Banasree", "Malibagh",
    "Shahbagh", "Dhanmondi", "New Market", "Azimpur", "Old Dhaka", "Gulistan", "Motijheel",
    "Kamalapur", "Jatrabari", "Uttara Sector 10", "Airport", "Bashundhara R/A", "Mohammadpur",
    "Shyamoli", "Gabtoli", "Savar", "Gazipur", "Narayanganj", "Keraniganj", "Tongi",
]

CHATTOGRAM_AREAS = [
    "Chattogram GEC Circle", "Agrabad", "Pahartali", "Halishahar", "Chawkbazar", "Patenga",
    "Karnaphuli", "Sitakunda", "Hathazari", "Cox's Bazar", "Teknaf", "Feni", "Cumilla",
    "Chandpur", "Noakhali", "Brahmanbaria", "Rangamati", "Bandarban", "Khagrachhari",
]

OTHER_DIVISIONS = [
    "Sylhet Zindabazar", "Sylhet Amberkhana", "Moulvibazar", "Habiganj", "Sunamganj",
    "Rajshahi", "Bogura", "Pabna", "Natore", "Sirajganj", "Naogaon", "Chapainawabganj",
    "Khulna", "Jashore", "Satkhira", "Kushtia", "Bagerhat", "Magura",
    "Barishal", "Bhola", "Patuakhali", "Pirojpur",
    "Rangpur", "Dinajpur", "Saidpur", "Kurigram", "Thakurgaon", "Gaibandha",
    "Mymensingh", "Jamalpur", "Netrokona", "Sherpur",
    "Tangail", "Faridpur", "Gopalganj", "Madaripur", "Manikganj", "Kishoreganj",
]

AREAS = DHAKA_AREAS + CHATTOGRAM_AREAS + OTHER_DIVISIONS
