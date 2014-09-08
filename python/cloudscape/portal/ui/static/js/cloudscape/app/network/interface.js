cs.import('CSNetworkInterface', function() {
	
	/**
	 * Initialize CSNetworkInterface
	 * @constructor
	 */
	this.__init__ = function() {
		
		// Routers
		if (defined(cs.url.param_get('router'))) {
			cs.implement('CSNetworkRouterDetails', 'network.router');
			
		} else {
			if (cs.url.param_get('panel') == 'routers') {
				cs.implement('CSNetworkRoutersList', 'network.router');
			}
		}
	}
});