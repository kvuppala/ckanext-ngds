
ngds.render_search_results = function(topic,result) { //Subscription - 'Map.result_received'
	var seq = new ngds.util.sequence_generator();
	var count = result['count'];
	var results = result['results'];
	var query = result['query'];
	ngds.log("Received "+count+" results : "+results,results);
	$(".results").remove();
	var clazz = "results";
	
	if(ngds.Map.is_fullscreen()===true) {
		clazz = clazz + " large";
	}

	$(".map-search-results").prepend($("<div/>",{"class":clazz,"id":"results"}));
	for(var i=0;i<results.length;i++) {
		
		for(var j=0;j<results[i].resources.length;j++) {
			console.log(results[i].resources[j].ogc_type);
		}

		results[i]["type"] = results[i]["type"][0].toUpperCase() + results[i]["type"].slice(1,results[i]["type"].length);
		
		var skeleton = {
			'tag':'div',
			'attributes':{
				'class':'result result-'+seq.next()
			},
			'children':[
				{
					'tag':'p',
					'attributes':{
						'class':'description-wrapper'
					},
					'children':[
						{
							'tag':'a',
							'attributes':{
								'class':'description',
								'href':['/dataset',results[i]['name']].join('/'),
								'target':'_blank',
								'text':ngds.util.get_n_chars(results[i]['title'],38)
							}
						}
						]
					
				},
				{
					'tag':'p',
					'attributes':{
						'class':'notes',
						'text':ngds.util.get_n_chars(results[i]['notes'],58)
					}
				},
				{
					'tag':'div',
					'attributes':{
						'class':'additional-dataset-info'
					},
					'children':[
							{
							'tag':'p',
							'attributes':{
								'class':'type',
								'text':results[i]['type']
								}
							},
							{
							'tag':'p',
							'attributes':{
								'class':'published',
								'text':"Published "+new Date(results[i]['metadata_created']).toLocaleDateString()
								}
							}
					]
				}
				
				// {
				// 	'tag':'button',
				// 	'attributes':{
				// 		'class':'wms',
				// 		'id':results[i]['resources'][0]['id'],
				// 		'text':"WMS"
				// 	}
				// },
				
			]
		};
		var shaped_loop_scope = ngds.ckandataset(results[i]).get_feature_type()['type'];
		var marker_container = { };
		var alph_seq = seq.current('alph');
		ngds.publish('Map.feature_received',{
				'feature':results[i],
				'seq':seq.current(),
                'alph_seq':alph_seq
			});

		if(shaped_loop_scope==='Point') {	
			marker_container = {
				'tag':'div',
				'attributes':{
					'class':'result-marker-container marker-'+seq.current()
				},
				'priority':1,
				'children':[
					{
						'tag':'img',
						'attributes':{
							'src':'/images/marker.png',
							'class':'result-marker'
						}
					},
					{
						'tag':'span',
						'attributes':{
							'class':'result-marker-label marker-label-'+seq.current(),
							'text':alph_seq
						}
					}
				]
			};
			skeleton['children'].push(marker_container);
		}

		var dom_node = ngds.util.dom_element_constructor(skeleton);
		$('.results').prepend(dom_node);
		var reader = ngds.util.dom_element_constructor({
			'tag':'div',
			'attributes':{
				'class':'results-text'
			},
			'children':[{
				'tag':'p',
				'attributes':{
					'text':'Found '+count+" results for \""+query+"\"",
					'class':'reader'
				}
			}
			]
		});
	}
	$('.results').before(reader);
	$(".results").jScrollPane({contentWidth:'0px'});

	var inc=inc || (inc=0);
	$(".wms").click(function(ev){
				var id=ev.currentTarget.id;
						var ngds_layer = L.tileLayer.wms('http://'+window.location.hostname+":8080/geoserver/NGDS/wms",{
						layers:"NGDS:"+id,
						format: 'image/png',
					    transparent: true,
					    attribution: "NGDS",
					    tileSize:128,
					    opacity:'0.9999'
					});

				layer_control.addOverlay(ngds_layer,"WMS"+inc);
				inc++;
			});

};

ngds.subscribe('Map.results_received',ngds.render_search_results);