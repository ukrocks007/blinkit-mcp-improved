# 🤖 Automated Blinkit API Discovery Report
Generated: 2026-02-01 09:31:20

## 📊 Discovery Statistics
- **Total API Calls Captured**: 242
- **Authentication Tokens Found**: 4
- **Discovery Method**: Automated (Raspberry Pi + Playwright)

## 🔐 Authentication Analysis
**🎯 Authentication Headers Found:**
- `auth_key`: `c761ec3633c22afad934...`
- `session_uuid`: `ee9927aa-836b-4e54-9...`
- `access_token`: `v2::d3aa89b0-024c-44...`
- `feature_flag_key`: `14084948`

## 📡 Discovered API Endpoints

### 🔹 Authentication (2 endpoints)

**GET** `https://blinkit.com/v2/services/secondary-data/` *(Called 2 times)*
**GET** `https://blinkit.com/v2/services/secondary-data`

### 🔹 Search (3 endpoints)

**GET** `https://blinkit.com/v2/search/deeplink/`
**POST** `https://blinkit.com/v1/layout/empty_search`
**POST** `https://blinkit.com/v1/layout/search` *(Called 10 times)*

### 🔹 Cart (1 endpoints)

**POST** `https://blinkit.com/v5/carts`

### 🔹 Addresses (1 endpoints)

**GET** `https://blinkit.com/v4/address`

### 🔹 Orders (1 endpoints)

**GET** `https://blinkit.com/v1/order_count`

### 🔹 User (2 endpoints)

**POST** `https://jumbo.blinkit.com/event` *(Called 93 times)*
**GET** `https://blinkit.com/v1/user/user_property/14084948`

### 🔹 Other (3 endpoints)

**GET** `https://blinkit.com/api/feature-flags/receive` *(Called 3 times)*
**GET** `https://blinkit.com/v1/consumerweb/eta`
**POST** `https://blinkit.com/v1/actions/auto_suggest` *(Called 5 times)*


## 🎯 API Integration Assessment

**Total Unique Endpoints Discovered**: 13
**Critical Categories Found**: 4/5

✅ **Authentication**: 2 endpoints discovered
✅ **Search**: 3 endpoints discovered
✅ **Cart**: 1 endpoints discovered
❌ **Checkout**: No endpoints found
✅ **Addresses**: 1 endpoints discovered

**🚀 API Integration Feasibility**: 80%

🎉 **EXCELLENT**: Full API integration highly recommended!
   → Proceed with direct API implementation
   → Expected 99%+ reliability and 10x speed improvement
