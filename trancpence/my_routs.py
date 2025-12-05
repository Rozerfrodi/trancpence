from rest_framework import routers

class MyRouter(routers.SimpleRouter):
	routes = [
		routers.Route(
			url=r'^{prefix}/$',
			mapping={
					'get': 'list',
			        'post': 'create'
			         },
			name='{basename}-list',
			detail=False,
			initkwargs={'suffix': 'List'}
		),
		routers.Route(
			url=r'^{prefix}/{lookup}/$',
			mapping={
				'get': 'retrieve',
				'patch': 'update',
				'delete': 'destroy'
			},
			name='{basename}-detail',
			detail=True,
			initkwargs={'suffix': 'Detail'}
		),
		routers.DynamicRoute(
			url=r'^{prefix}/{url_path}{trailing_slash}$',
			name='{basename}-{url_name}',
			detail=False,
			initkwargs={}
		),
		routers.DynamicRoute(
			url=r'^{prefix}/{url_path}{trailing_slash}$',
			name='{basename}-{url_name}',
			detail=True,
			initkwargs={}
		)
	]

