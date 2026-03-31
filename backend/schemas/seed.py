"""Seed data: 50 tech companies with their identifiers across sources."""

COMPANIES: list[dict] = [
    # Tech Giants
    {"name": "Apple", "ticker": "AAPL", "wiki": "Apple_Inc.", "github": "apple", "cik": "0000320193"},
    {"name": "Microsoft", "ticker": "MSFT", "wiki": "Microsoft", "github": "microsoft", "cik": "0000789019"},
    {"name": "Google", "ticker": "GOOGL", "wiki": "Alphabet_Inc.", "github": "google", "cik": "0001652044"},
    {"name": "Meta", "ticker": "META", "wiki": "Meta_Platforms", "github": "facebookresearch", "cik": "0001326801"},
    {"name": "Amazon", "ticker": "AMZN", "wiki": "Amazon_(company)", "github": "aws", "cik": "0001018724"},
    {"name": "NVIDIA", "ticker": "NVDA", "wiki": "Nvidia", "github": "NVIDIA", "cik": "0001045810"},
    {"name": "Tesla", "ticker": "TSLA", "wiki": "Tesla,_Inc.", "github": "teslamotors", "cik": "0001318605"},

    # AI Companies
    {"name": "Anthropic", "ticker": None, "wiki": "Anthropic", "github": "anthropic", "cik": None},
    {"name": "OpenAI", "ticker": None, "wiki": "OpenAI", "github": "openai", "cik": None},
    {"name": "Mistral", "ticker": None, "wiki": "Mistral_AI", "github": "mistralai", "cik": None},
    {"name": "Cohere", "ticker": None, "wiki": "Cohere_(company)", "github": "cohere-ai", "cik": None},
    {"name": "Hugging Face", "ticker": None, "wiki": "Hugging_Face", "github": "huggingface", "cik": None},

    # Enterprise Software
    {"name": "Salesforce", "ticker": "CRM", "wiki": "Salesforce", "github": "salesforce", "cik": "0001108524"},
    {"name": "Palantir", "ticker": "PLTR", "wiki": "Palantir_Technologies", "github": "palantir", "cik": "0001321655"},
    {"name": "Snowflake", "ticker": "SNOW", "wiki": "Snowflake_Inc.", "github": "snowflakedb", "cik": "0001640147"},
    {"name": "Databricks", "ticker": None, "wiki": "Databricks", "github": "databricks", "cik": None},
    {"name": "HashiCorp", "ticker": "HCP", "wiki": "HashiCorp", "github": "hashicorp", "cik": "0001720671"},
    {"name": "MongoDB", "ticker": "MDB", "wiki": "MongoDB", "github": "mongodb", "cik": "0001441816"},

    # Cloud & Infra
    {"name": "Cloudflare", "ticker": "NET", "wiki": "Cloudflare", "github": "cloudflare", "cik": "0001477333"},
    {"name": "Vercel", "ticker": None, "wiki": "Vercel", "github": "vercel", "cik": None},
    {"name": "Supabase", "ticker": None, "wiki": "Supabase", "github": "supabase", "cik": None},
    {"name": "PlanetScale", "ticker": None, "wiki": "PlanetScale", "github": "planetscale", "cik": None},

    # Fintech
    {"name": "Stripe", "ticker": None, "wiki": "Stripe,_Inc.", "github": "stripe", "cik": None},
    {"name": "Plaid", "ticker": None, "wiki": "Plaid_(company)", "github": "plaid", "cik": None},

    # Consumer Tech
    {"name": "Netflix", "ticker": "NFLX", "wiki": "Netflix", "github": "netflix", "cik": "0001065280"},
    {"name": "Spotify", "ticker": "SPOT", "wiki": "Spotify", "github": "spotify", "cik": None},
    {"name": "Airbnb", "ticker": "ABNB", "wiki": "Airbnb", "github": "airbnb", "cik": "0001559720"},
    {"name": "Uber", "ticker": "UBER", "wiki": "Uber", "github": "uber", "cik": "0001543151"},
    {"name": "DoorDash", "ticker": "DASH", "wiki": "DoorDash", "github": "doordash", "cik": "0001792789"},

    # Semiconductors
    {"name": "AMD", "ticker": "AMD", "wiki": "AMD", "github": "GPUOpen-LibrariesAndSDKs", "cik": "0000002488"},
    {"name": "Intel", "ticker": "INTC", "wiki": "Intel", "github": "intel", "cik": "0000050863"},
    {"name": "Qualcomm", "ticker": "QCOM", "wiki": "Qualcomm", "github": "qualcomm", "cik": "0000804328"},
    {"name": "Broadcom", "ticker": "AVGO", "wiki": "Broadcom_Inc.", "github": "Broadcom", "cik": "0001649338"},

    # Enterprise Legacy
    {"name": "Oracle", "ticker": "ORCL", "wiki": "Oracle_Corporation", "github": "oracle", "cik": "0001341439"},
    {"name": "SAP", "ticker": "SAP", "wiki": "SAP", "github": "SAP", "cik": "0001000184"},
    {"name": "IBM", "ticker": "IBM", "wiki": "IBM", "github": "IBM", "cik": "0000051143"},
    {"name": "Adobe", "ticker": "ADBE", "wiki": "Adobe_Inc.", "github": "adobe", "cik": "0000796343"},

    # Cybersecurity
    {"name": "CrowdStrike", "ticker": "CRWD", "wiki": "CrowdStrike", "github": "CrowdStrike", "cik": "0001535527"},
    {"name": "Palo Alto Networks", "ticker": "PANW", "wiki": "Palo_Alto_Networks", "github": "PaloAltoNetworks", "cik": "0001327567"},
    {"name": "Fortinet", "ticker": "FTNT", "wiki": "Fortinet", "github": "fortinet", "cik": "0001262039"},

    # Dev Tools
    {"name": "GitLab", "ticker": "GTLB", "wiki": "GitLab", "github": "gitlabhq", "cik": "0001653482"},
    {"name": "Atlassian", "ticker": "TEAM", "wiki": "Atlassian", "github": "atlassian", "cik": "0001650372"},
    {"name": "JetBrains", "ticker": None, "wiki": "JetBrains", "github": "JetBrains", "cik": None},
    {"name": "Elastic", "ticker": "ESTC", "wiki": "Elastic_NV", "github": "elastic", "cik": "0001707753"},

    # Networking & Communication
    {"name": "Cisco", "ticker": "CSCO", "wiki": "Cisco", "github": "cisco", "cik": "0000858877"},
    {"name": "Twilio", "ticker": "TWLO", "wiki": "Twilio", "github": "twilio", "cik": "0001447669"},
    {"name": "Zoom", "ticker": "ZM", "wiki": "Zoom_Video_Communications", "github": "zoom", "cik": "0001585521"},

    # E-commerce / Payments
    {"name": "Shopify", "ticker": "SHOP", "wiki": "Shopify", "github": "Shopify", "cik": "0001594805"},
    {"name": "Block", "ticker": "SQ", "wiki": "Block,_Inc.", "github": "square", "cik": "0001512673"},
    {"name": "PayPal", "ticker": "PYPL", "wiki": "PayPal", "github": "paypal", "cik": "0001633917"},
]
