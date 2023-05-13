from app import application
from flask import jsonify, Response, session
from app.models import *
from app import *
import uuid
import datetime
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import json

#  Restful way of creating APIs through Flask Restful

class SignUpApiParams(Schema):
    name = fields.Str(required=True, default="name")
    username = fields.Str(required=True, default="username")
    password = fields.Str(required=True, default="password")
    level = fields.Int(required=True, default=0)

class LoginAPIParams(Schema):
    username = fields.Str(required=True, default='username')
    password = fields.Str(required=True, default='password')

class AddVendorAPIParams(Schema):
    user_id = fields.Str(required=True, default='user_id')

class AddItemAPIParams(Schema):
    item_name = fields.Str(required=True, default="default_item_name")
    restaurant_name = fields.Str(required=True, default="default_restaurant")
    available_quantity = fields.Int(default=0)
    unit_price = fields.Int(default=0)
    calories_per_gm = fields.Int(default=0)

class ItemOrderListParams(Schema):
    items = fields.List(fields.Dict())

# class PlaceOrderAPIParams(Schema):
#     customer_id = fields.Str(required=True, default="user_id")
#     vendor_id = fields.Str(required=True, default="vendor_id")
#     item_id = fields.Str(required=True, default="default_item_id")
#     quantity = fields.Int(required=True, default=0)

class PlaceOrderAPIParams(Schema):
    order_id = fields.String(default="default_str")

class ListOrdersByCustomerAPIParams(Schema):
    customer_id = fields.Str(required=True, default="user_id")

class APIResponce(Schema):
    message = fields.Str(default="default message")

# class ListVendorsResponce(Schema):
#     vendors = fields.List(fields.Dict(keys=fields.Str(), values=fields.Str()))

# class ListItemsAPIResponce(Schema):
#     items = fields.List(fields.Dict(keys=fields.String(), values=fields.String()))

# class ListOrdersAPIResponce(Schema):
#     orders = fields.List(fields.Dict(keys=fields.String(), values=fields.String()))

class CommonAPIViewResponce(Schema):
    Responce = fields.List(fields.Dict(keys=fields.String(), values=fields.String()))

dic_string = '''
SignUp API
User level = 0,
Vendor level = 1,
Admin level = 2
'''


class SignUpAPI(MethodResource, Resource):
    @doc(description=dic_string, tags=['USLL API'])
    @use_kwargs(SignUpApiParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            user = User(
                user_id = uuid.uuid4(),
                name = kwargs['name'],
                username = kwargs['username'],
                password = kwargs['password'],
                level = kwargs['level']
            )
            db.session.add(user)
            db.session.commit()
            return APIResponce().dump(dict(message=f'User {kwargs["username"]} Successfully Created')), 200
        except Exception as e:
            return APIResponce().dump(dict(message=f'error while creating User, error{str(e)}')), 404

api.add_resource(SignUpAPI, '/signup')
docs.register(SignUpAPI)

class LoginAPI(MethodResource, Resource):
    @doc(description="LoginAPI", tags=['USLL API'])
    @use_kwargs(LoginAPIParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            user = User.query.filter_by(username=kwargs['username'], password=kwargs['password']).first()
            if user:
                session['user_id'] = user.user_id
                return APIResponce().dump(dict(message=f"{user.user_id}, {user.username} Logged in Successfully")), 200
            return APIResponce().dump(dict(message=f"User {kwargs['username']} does not exist. Try signing up or check credentials.")), 401
        except Exception as e:
            return APIResponce().dump(dict(message=f"error while loggin the user, error {str(e)}")), 404
            

api.add_resource(LoginAPI, '/login')
docs.register(LoginAPI)

class LogoutAPI(MethodResource, Resource):
    @doc(description="Logout User", tags=['USLL API'])
    @marshal_with(APIResponce)
    def get(self):
        try:
            if 'user_id' in session:
                session.clear()
                return APIResponce().dump(dict(message="Logged out Successfully")), 200
            return APIResponce().dump(dict(message="User not logged in or Logged out")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"Something went wrong, error: {str(e)}")), 404
            

api.add_resource(LogoutAPI, '/logout')
docs.register(LogoutAPI)


class AddVendorAPI(MethodResource, Resource):
    @doc(description="only Admins can make available users as vendors", tags=['Vendor APIs'])
    @use_kwargs(AddVendorAPIParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            if 'user_id' in session.keys():
                user_id = session['user_id']
                user_type = User.query.filter_by(user_id=user_id).first().level
                if user_type == 2:
                    vendor_id = kwargs['user_id']
                    user = User.query.filter_by(user_id=vendor_id).first()
                    user.level = 1
                    db.session.commit()
                    return APIResponce().dump(dict(message=f"{vendor_id} {user.username} made as vendor successfully")), 200
                return APIResponce().dump(dict(message="you need to be admin to makke changes to users")), 405
            return APIResponce().dump(dict(message="login to make changes")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"Adding as venndor failed, error: {str(e)}")), 404
            

api.add_resource(AddVendorAPI, '/add_vendor')
docs.register(AddVendorAPI)


class GetVendorsAPI(MethodResource, Resource):
    @doc(description="only Admins can list all the vendors", tags=['Vendor APIs'])
    # @marshal_with(APIResponce)
    def get(self):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                print(user_id)
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 2:
                    vendors = User.query.filter_by(level=1)
                    vendor_list = []
                    for vendor in vendors:
                        item = {
                            "vendor_id": vendor.user_id,
                            "vendor_name": vendor.name,
                            "vendor_username": vendor.username
                        }
                        vendor_list.append(item)
                    return CommonAPIViewResponce().dump(dict(Responce=vendor_list)), 200
                return APIResponce().dump(dict(message="you need to be admin to view vendors list")), 405
            return APIResponce().dump(dict(message="login to check vendor list")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"Error while listing vendors, error: {str(e)}")), 404

api.add_resource(GetVendorsAPI, '/list_vendors')
docs.register(GetVendorsAPI)

class AddItemAPI(MethodResource, Resource):
    @doc(description="Add items", tags=['Item APIs'])
    @use_kwargs(AddItemAPIParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                print(session['user_id'])
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 1:
                    item = Item(
                        vendor_id = user_id,
                        item_id = uuid.uuid4(),
                        item_name = kwargs['item_name'],
                        restaurant_name = kwargs['restaurant_name'],
                        unit_price = kwargs['unit_price'],
                        available_quantity = kwargs['available_quantity'],
                        calories_per_gm = kwargs['calories_per_gm']
                    )
                    db.session.add(item)
                    db.session.commit()
                    return APIResponce().dump(dict(message=f"Item {kwargs['item_name']} added successfully")), 200
                return APIResponce().dump(dict(message="Need to be a vendor to add items")), 405
            return APIResponce().dump(dict(message="Need to login first")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"item not added, error: {str(e)}")), 404

api.add_resource(AddItemAPI, '/add_item')
docs.register(AddItemAPI)


class ListItemsAPI(MethodResource, Resource):
    @doc(description="get list of items available", tags=['Item APIs'])
    # @marshal_with(ListItemsAPIResponce)
    def get(self):
        try:
            items = Item.query.all()
            item_list = []
            for item in items:
                if item.available_quantity > 0:
                    appendable_item = {
                        "item_id": item.item_id,
                        "item_name": item.item_name,
                        "restaurant_name": item.restaurant_name,
                        "unit_price": item.unit_price,
                        "available_quantity": item.available_quantity,
                        "calories_per_gm": item.calories_per_gm,
                        "vendor": item.vendor_id
                    }
                    item_list.append(appendable_item)
            return CommonAPIViewResponce().dump(dict(Responce=item_list)), 200
        except Exception as e:
            return APIResponce().dump(dict(message=f"Not able to list the products, error: {str(e)}")), 404


api.add_resource(ListItemsAPI, '/list_items')
docs.register(ListItemsAPI)


class CreateItemOrderAPI(MethodResource, Resource):
    @doc(description="creaet items order", tags=['Order APIs'])
    @use_kwargs(ItemOrderListParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 0:
                    order_id = uuid.uuid4()
                    order = Order(order_id=order_id, user_id=user_id)
                    db.session.add(order)
                    for item in kwargs['items']:
                        item = dict(item)
                        order_item = OrderItems(
                            id = uuid.uuid4(),
                            order_id = order_id,
                            item_id = item['item_id'],
                            quantity = item['quantity']
                        )
                        db.session.add(order_item)
                    db.session.commit()
                    return APIResponce().dump(dict(message=f"order with item successfully created with order id: {order_id}")), 200
                return APIResponce().dump(dict(message="logged in user is not a Customer")), 405
            return APIResponce().dump(dict(message="user must login")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"cannot create order, error: {str(e)}")), 404

api.add_resource(CreateItemOrderAPI, '/create_items_order')
docs.register(CreateItemOrderAPI)


class PlaceOrderAPI(MethodResource, Resource):
    @doc(description="place an order", tags=['Order APIs'])
    @use_kwargs(PlaceOrderAPIParams, location=('json'))
    @marshal_with(APIResponce)
    def post(self, **kwargs):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 0:
                    # customer_id = kwargs['custimer_id']
                    # if user_id == customer_id:
                    #     vendor_id = kwargs['vendor_id']
                    #     item_id = kwargs['item_id']
                    #     quantity = kwargs['quantity']
                    order_id = kwargs['order_id']
                    order_items = OrderItems.query.filter_by(order_id=order_id, is_active=1)
                    order = Order.query.filter_by(order_id=order_id, is_active=1).first()
                    total_amount = 0
                    for order_item in order_items:
                        item_id = order_item.item_id
                        item = Item.query.filter_by(item_id=item_id, is_active=1).first()
                        total_amount += order_item.quantity * item.unit_price
                        item.available_quantity -= order_item.quantity
                    order.total_amount = total_amount
                    db.session.commit()
                    return APIResponce().dump(dict(message="Order placed successfully")), 200
                return APIResponce().dump(dict(message="logged in user must be a customer")), 405
            return APIResponce().dump(dict(message="Must be logged in to place order")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"Cannot place order at the momnet, error: {str(e)}")), 404

api.add_resource(PlaceOrderAPI, '/place_order')
docs.register(PlaceOrderAPI)

class ListOrdersByCustomerAPI(MethodResource, Resource):
    @doc(description="list of orders placed by customer", tags=['Order APIs'])
    @use_kwargs(ListOrdersByCustomerAPIParams, location=('json'))
    def post(self, **kwargs):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 0:
                    orders = Order.query.filter_by(user_id=user_id, is_active=1)
                    orders_list = []
                    for order in orders:
                        order_items = OrderItems.query.filter_by(order_id = order.order_id, is_active=1)
                        order_dict = dict()
                        order_dict['order_id'] = order.order_id
                        order_dict['items'] = []
                        for item in order_items:
                            appendable_item = {
                                "item_id": item.item_id,
                                "quantity": item.quantity 
                            }
                            order_dict['items'].append(appendable_item)
                        orders_list.append(order_dict)
                    return CommonAPIViewResponce().dump(dict(Responce=orders_list)), 200
                return APIResponce().dump(dict(message="Need to login as customer")), 405
            return APIResponce().dump(dict(message="Need to login")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"Could not get list of orders, error: {str(e)}")), 404

api.add_resource(ListOrdersByCustomerAPI, '/list_orders')
docs.register(ListOrdersByCustomerAPI)


class ListAllOrdersAPI(MethodResource, Resource):
    @doc(description="All orders placed till now", tags=['Order APIs'])
    # @marshal_with(APIResponce)
    def get(self):
        try:
            if 'user_id' in session:
                user_id = session['user_id']
                user_level = User.query.filter_by(user_id=user_id).first().level
                if user_level == 2:
                    orders = Order.query.filter_by(is_active=1)
                    orders_list = []
                    for order in orders:
                        order_items = OrderItems.query.filter_by(order_id=order.order_id, is_active=1)
                        order_dict = dict()
                        order_dict['order_id'] = order.order_id
                        order_dict['items'] = list()
                        for item in order_items:
                            appendable_item = {
                                "item_id": item.item_id,
                                "quantity": item.quantity
                            }
                            order_dict['items'].append(appendable_item)
                        orders_list.append(order_dict)
                    return CommonAPIViewResponce().dump(dict(Responce=orders_list)), 200
                return APIResponce().dump(dict(message="you need Admin Privillages to view all orders")), 405
            return APIResponce().dump(dict(message="Login as Admin")), 406
        except Exception as e:
            return APIResponce().dump(dict(message=f"could not get list of orders, error: {str(e)}")), 404
            
api.add_resource(ListAllOrdersAPI, '/list_all_orders')
docs.register(ListAllOrdersAPI)