-- Every customer who's shown up in a sale, enriched with loyalty info
-- where it exists. Not every customer is a loyalty member.
with sale_customers as (
    select distinct customer_email from {{ ref('fct_sales') }}
)

select
    sale_customers.customer_email,
    loyalty.member_id,
    loyalty.full_name,
    loyalty.signup_date,
    loyalty.loyalty_tier
from sale_customers
left join {{ ref('stg_loyalty_members') }} loyalty
    on sale_customers.customer_email = loyalty.email
