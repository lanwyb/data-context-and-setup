import pandas as pd
import numpy as np
from olist.utils import haversine_distance
from olist.data import Olist
import datetime


class Order:
    '''
    DataFrames containing all orders as index,
    and various properties of these orders as columns
    '''
    def __init__(self):
        # Assign an attribute ".data" to all new instances of Order
        self.data = Olist().get_data()

    def get_wait_time(self, is_delivered=True):
        """
        Returns a DataFrame with:
        [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]
        and filters out non-delivered orders unless specified
        """

        # YOUR CODE HERE
        orders = self.data['orders']


        # handle date time
        orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
        orders['order_approved_at'] = pd.to_datetime(orders['order_approved_at'])
        orders['order_delivered_carrier_date'] = pd.to_datetime(orders['order_delivered_carrier_date'])
        orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'])
        orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'])

        # compute waittime
        one_day_delta = datetime.timedelta(days=1)

        orders['wait_time'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp'])/one_day_delta
        # expected_wait_time
        orders['expected_wait_time'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp'])/one_day_delta

        # delay_vs_expected
        # order_delivered_customer_date is later than the estimated delivery date,
        # returns the number of days between the two dates, otherwise return 0

        if is_delivered:
            orders = orders[orders['order_status'] == 'delivered']

        orders['delay_vs_expected'] = orders["delay_vs_expected"] = (
            orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
        ).apply(lambda x: max(pd.Timedelta(x).total_seconds() / (24 * 60 * 60), 0) if x > pd.Timedelta(0) else 0)

        ## [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]

        return orders[['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected', 'order_status']]

    def get_review_score(self):
        """
        Returns a DataFrame with:
        order_id, dim_is_five_star, dim_is_one_star, review_score
        """
        reviews = self.data['order_reviews']
        reviews['dim_is_five_star'] = reviews['review_score'].map(lambda x: 1 if x == 5 else 0)
        reviews['dim_is_one_star'] = reviews['review_score'].map(lambda x: 1 if x == 1 else 0)
        return reviews[['order_id', 'dim_is_five_star', 'dim_is_one_star', 'review_score']]

    def get_number_items(self):
        """
        Returns a DataFrame with:
        order_id, number_of_items
        """
        order_items = self.data['order_items']
        count_items = order_items.groupby('order_id')['order_item_id'].count()
        df = pd.DataFrame(count_items).reset_index()
        df = df.rename(columns={'order_item_id': "number_of_items" })
        return df

    def get_number_sellers(self):
        """
        Returns a DataFrame with:
        order_id, number_of_sellers
        """
        sellers = self.data['sellers']
        order_items = self.data['order_items']
        merged_sellers = sellers.merge(order_items, on = 'seller_id')
        merged_sellers = merged_sellers.groupby('order_id')['seller_id'].nunique()
        df = pd.DataFrame(merged_sellers)
        df = df.reset_index().rename(columns = {'seller_id' : 'number_of_sellers' })
        return df

    def get_price_and_freight(self):
        """
        Returns a DataFrame with:
        order_id, price, freight_value
        """
        order_items = self.data['order_items']
        order_items = order_items.drop_duplicates(subset=['order_id'])
        return order_items[['order_id','price','freight_value']]

    # Optional
    def get_distance_seller_customer(self):
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        # import data
        data = self.data
        orders = data['orders']
        order_items = data['order_items']
        sellers = data['sellers']
        customers = data['customers']

        # Since one zip code can map to multiple (lat, lng), take the first one
        geo = data['geolocation']
        geo = geo.groupby('geolocation_zip_code_prefix',
                          as_index=False).first()

        # Merge geo_location for sellers
        sellers_mask_columns = [
            'seller_id', 'seller_zip_code_prefix', 'geolocation_lat', 'geolocation_lng'
        ]

        sellers_geo = sellers.merge(
            geo,
            how='left',
            left_on='seller_zip_code_prefix',
            right_on='geolocation_zip_code_prefix')[sellers_mask_columns]

        # Merge geo_location for customers
        customers_mask_columns = ['customer_id', 'customer_zip_code_prefix', 'geolocation_lat', 'geolocation_lng']

        customers_geo = customers.merge(
            geo,
            how='left',
            left_on='customer_zip_code_prefix',
            right_on='geolocation_zip_code_prefix')[customers_mask_columns]

        # Match customers with sellers in one table
        customers_sellers = customers.merge(orders, on='customer_id')\
            .merge(order_items, on='order_id')\
            .merge(sellers, on='seller_id')\
            [['order_id', 'customer_id','customer_zip_code_prefix', 'seller_id', 'seller_zip_code_prefix']]

        # Add the geoloc
        matching_geo = customers_sellers.merge(sellers_geo,
                                            on='seller_id')\
            .merge(customers_geo,
                   on='customer_id',
                   suffixes=('_seller',
                             '_customer'))
        # Remove na()
        matching_geo = matching_geo.dropna()

        matching_geo.loc[:, 'distance_seller_customer'] =\
            matching_geo.apply(lambda row:
                               haversine_distance(row['geolocation_lng_seller'],
                                                  row['geolocation_lat_seller'],
                                                  row['geolocation_lng_customer'],
                                                  row['geolocation_lat_customer']),
                               axis=1)
        # Since an order can have multiple sellers,
        # return the average of the distance per order
        order_distance =\
            matching_geo.groupby('order_id',
                                 as_index=False).agg({'distance_seller_customer':
                                                      'mean'})

        return order_distance

    def get_training_data(self,
                          is_delivered=True,
                          with_distance_seller_customer=False):
        """
        Returns a clean DataFrame (without NaN), with the all following columns:
        ['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected',
        'order_status', 'dim_is_five_star', 'dim_is_one_star', 'review_score',
        'number_of_items', 'number_of_sellers', 'price', 'freight_value',
        'distance_seller_customer']
        """
        wait_time = self.get_wait_time()
        review_score = self.get_review_score()
        number_items = self.get_number_items()
        number_sellers = self.get_number_sellers()
        price_and_freight = self.get_price_and_freight()

        df = wait_time.merge(review_score, on='order_id') \
              .merge(number_items, on='order_id') \
              .merge(number_sellers, on='order_id') \
              .merge(price_and_freight, on='order_id')

        if with_distance_seller_customer:
            df = df.merge(
                self.get_distance_seller_customer(), on='order_id')
        return df.dropna()
