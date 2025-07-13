from decimal import Decimal
import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import re
from datetime import datetime
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from .filters import CustomerFilter, ProductFilter, OrderFilter

# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        interfaces = (relay.Node, )

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (relay.Node, )

    # Override the price field to handle Decimal conversion
    price = graphene.Float()

    def resolve_price(self, info):
        return float(self.price)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")
        interfaces = (relay.Node, )

    # Override products to return a simple list instead of connection
    products = graphene.List(ProductType)

    # Override total_amount to handle Decimal conversion
    total_amount = graphene.Float()

    def resolve_products(self, info):
        return self.products.all()
    
    def resolve_total_amount(self, info):
        return float(self.total_amount)

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(message="Email already exists.")
        if input.phone:
            phone_pattern = r"^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$"
            if not re.match(phone_pattern, input.phone):
                return CreateCustomer(message="Invalid phone format.")
        customer = Customer(name=input.name, email=input.email, phone=input.phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        customers = []
        errors = []
        with transaction.atomic():
            for idx, data in enumerate(input):
                if Customer.objects.filter(email=data.email).exists():
                    errors.append(f"Row {idx+1}: Email already exists.")
                    continue
                if data.phone:
                    phone_pattern = r"^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$"
                    if not re.match(phone_pattern, data.phone):
                        errors.append(f"Row {idx+1}: Invalid phone format.")
                        continue
                customer = Customer(name=data.name, email=data.email, phone=data.phone)
                customer.save()
                customers.append(customer)
        return BulkCreateCustomers(customers=customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    def mutate(self, info, input):
        if input.price <= 0:
            return CreateProduct(message="Price must be positive.")
        if input.stock is not None and input.stock < 0:
            return CreateProduct(message="Stock cannot be negative.")
        product = Product(name=input.name, price=Decimal(str(input.price)), stock=input.stock or 0)
        product.save()
        return CreateProduct(product=product, message="Product created successfully.")

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    order = graphene.Field(OrderType)
    message = graphene.String()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except ObjectDoesNotExist:
            return CreateOrder(message="Invalid customer ID.")
        if not product_ids:
            return CreateOrder(message="At least one product must be selected.")
        products = []
        total = Decimal('0.00')
        for pid in product_ids:
            try:
                product = Product.objects.get(pk=pid)
                products.append(product)
                total += product.price
            except ObjectDoesNotExist:
                return CreateOrder(message=f"Invalid product ID: {pid}")
        order = Order(customer=customer, total_amount=total, order_date=order_date or datetime.now())
        order.save()
        order.products.set(products)
        return CreateOrder(order=order, message="Order created successfully.")
    
# Update Low Stock Products Mutation()==> REVERT
class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        # No arguments needed for this mutation
        pass

    class Meta:
        description = "Updates all products with stock < 10 by incrementing their stock by 10"

    # Return fields
    success = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)
    updated_count = graphene.Int()

    @classmethod
    def mutate(cls, root, info):
        try:
            with transaction.atomic():
                # Query products with stock < 10
                low_stock_products = Product.objects.filter(stock__lt=10)
                
                if not low_stock_products.exists():
                    return UpdateLowStockProducts(
                        success=True,
                        message="No low-stock products found",
                        updated_products=[],
                        updated_count=0
                    )
                
                # Store products for return and update them
                updated_products = []
                
                for product in low_stock_products:
                    product.stock += 10
                    product.save()
                    updated_products.append(product)
                
                return UpdateLowStockProducts(
                    success=True,
                    message=f"Successfully updated {len(updated_products)} low-stock products",
                    updated_products=updated_products,
                    updated_count=len(updated_products)
                )
                
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error updating products: {str(e)}",
                updated_products=[],
                updated_count=0
            )

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    # Update low stock products mutation ()==>REVERT
    update_low_stock_products = UpdateLowStockProducts.Field() 

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter, order_by=graphene.List(of_type=graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter, order_by=graphene.List(of_type=graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter, order_by=graphene.List(of_type=graphene.String))
    # customer = relay.Node.Field(CustomerType)
    # product = relay.Node.Field(ProductType)

schema = graphene.Schema(query=Query, mutation=Mutation)