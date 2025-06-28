import graphene


class Query(graphene.ObjectType):
    # Define query fields

    hello = graphene.String()

    def resolve_hello(self, info):
        return f"Hello, GraphQL!"
    
schema = graphene.Schema(query=Query)
