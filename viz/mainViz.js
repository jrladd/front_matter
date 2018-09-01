var graph,
    origGraph,
    currentGraph,
    projectedPeopleGraph,
    projectedTextGraph;

var dispatch = d3.dispatch("load", "update");

var svg = d3.select("#main-graph")
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 1400 1000")
    .classed("svg-content-responsive", true);

var width = +svg.attr("width")+1000;
    height = +svg.attr("height")+700-70;

const defaultStart = 1570,
      defaultEnd = 1580;

var color = d3.scaleLinear()
	.domain([1500,1700])
	.range([0.1,1]);

var panelMargin = {
    top: 0,
    right: 0,
    bottom: 10,
    left: 0
  }
  panelWidth = width/3 - panelMargin.left - panelMargin.right,
  panelHeight = (height/4) - panelMargin.top - panelMargin.bottom;

var panelX = d3.scaleLinear().range([4, panelWidth - 4]),
  panelY = d3.scaleLinear().range([panelHeight, 15]);

var centralityType = "degree";

dispatch.on("load.network", function() {
  svg.append('rect')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('fill', '#fff')
      .on("click", () => {
        node.classed("transparent", false);
        link.classed("transparent", false);
      });

  svg.append("defs").append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
    .append("path")
      .attr("d", "M0,-5L10,0L0,5");

  var simulation = d3.forceSimulation()
      .force("link", d3.forceLink().id(function(d) { return d.id; }).iterations(2))
      .force("charge", d3.forceManyBody().strength([-100]).distanceMax([350]))
      .force("center", d3.forceCenter(width / 3, height / 2))
      .force("collide", d3.forceCollide().iterations(0));


  var container = svg.append('g');
  var link = container.append('g').selectAll('.link');
  var node = container.append('g').selectAll('.node');

  // Call zoom for svg container.
  // svg.call(d3.zoom().on('zoom', () => { container.attr("transform", "translate(" + d3.event.transform.x + ", " + d3.event.transform.y + ") scale(" + d3.event.transform.k + ")"); }));

  function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
  }

  dispatch.on("update.network", function(graph, centralityType) {
    // Make object of all neighboring nodes.
    var linkedByIndex = {};
    graph.links.forEach(function(d) {
  	  linkedByIndex[d.source.id + ',' + d.target.id] = 1;
  	  linkedByIndex[d.target.id + ',' + d.source.id] = 1;
    });

    // A function to test if two nodes are neighboring.
    function neighboring(a, b) {
  	  return linkedByIndex[a.id + ',' + b.id];
    }

    // Linear scale for degree centrality.
    var degreeSize= d3.scaleLog()
    	.domain([d3.min(graph.nodes, function(d) { if (d.bipartite === 1) {return d.degree;} }),d3.max(graph.nodes, function(d) {if (d.bipartite === 1) {return d.degree;} })])
    	.range([5,20]);

    var arrowSize= d3.scaleLinear()
    	.domain([d3.min(graph.nodes, function(d) {return d.degree; }),d3.max(graph.nodes, function(d) {return d.degree; })])
    	.range([40,50]);

    simulation
        .nodes(graph.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(graph.links);

    //var link = container.append("g")
        //.attr("class", "links")
      //.selectAll("line")
    link = link.data(graph.links, function(d) { return d.source.id + ", " + d.target.id;});

    link.exit().remove();

    link = link.enter().append("line")
        .attr('class', 'link')
        // .attr('stroke-width', function(l) {return l.weight;})
        .attr("marker-end", "url(#arrow)")
        .merge(link);

    //var node = container.append("g")
        //.attr("class", "nodes")
      //.selectAll("circle")
      //.data(graph.nodes);

    node = node.data(graph.nodes, function(d) { return d.id; });
    node.exit().remove();

    node = node.enter().append("circle")
      // Calculate degree centrality within JavaScript.
      //.attr("r", function(d, i) { count = 0; graph.links.forEach(function(l) { if (l.source == i || l.target == i) { count += 1;}; }); return size(count);})
      // Size nodes, making Cavendish and Glanvill largest.
      .attr('r', function(d, i) {if (d.bipartite === 1) {return degreeSize(d.degree);} else {return 8;} })
      // Color by degree centrality calculation in NetworkX.
  	    .attr("fill", function(d) {if (d.bipartite === 0) {return d3.interpolateBlues(color(d.date));} })
        .attr('class', 'node')
        .classed('person', d => { if (d.bipartite === 1) {return true; } })
        .attr('id', function(d) { return "n" + d.id.toString(); })
        .on('click', function(d) { // On click, "unstick" nodes
          simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .merge(node);


    // Title text for mouseover.
    node.append("title")
        .text(function(d) {
  	 if (d.bipartite === 1) {
  	      return `${d.id}\nName Variants: ${d.name_variants}\nDegree: ${d.degree} (${d.deg_rank})`;
  	 }
  	 else {
  	      return `Author: ${d.author}\nTitle: ${d.title}\nDate: ${d.date}\nDegree: ${d.degree} (${d.deg_rank})`;
  	}
  	});



    //simulation.alphaTarget(0.1).restart();
        simulation.alpha(1);
        simulation.alphaDecay(0.05);
        simulation.restart();

    function ticked() {
      link
          .attr("x1", function(d) { return d.source.x; })
          .attr("y1", function(d) { return d.source.y; })
          .attr("x2", function(d) { return d.target.x; })
          .attr("y2", function(d) { return d.target.y; });
          // .attr("d", linkArc)

      node
          .attr("cx", function(d) { return d.x; })
          .attr("cy", function(d) { return d.y; });

      if (simulation.alpha() < 0.005 && simulation.force("collide").iterations() == 0) {
  	// Collision detection based on node radius.
  	simulation.force("collide", d3.forceCollide().radius( 20 ) );//function(d) { return d.degree * 2; } ) );
      }

    }
  })
})

dispatch.on("load.peopleGraph", function() {
  var peopleGraph = svg.append('g')
          .classed("panel-container", true)
          .attr('width', width/3)
          .attr('height', height/4)
          .attr("transform", "translate(" + width * (2/3) +",0)");

  peopleGraph.append("rect")
      .attr("width", "100%")
      .attr("height", height/2)
      .attr("fill", "#fff");


  dispatch.on("update.peopleGraph", function(graph, centralityType) {
    let projectedGraph = project(graph, 1);

    createNxGraph(projectedGraph, centralityType).then(sortedData => {

      let data = sortedData.map(s => s[1][`local_${centralityType}`]);

      panelX.domain(d3.extent(data));

      let bins = d3.histogram()
        .domain(panelX.domain())
        // .thresholds(20)
      (data)

      panelY.domain([0, d3.max(bins, d => d.length)])

      peopleGraph.selectAll("g").remove();

      var peopleG = peopleGraph.append("g");

      var peopleBar = peopleG.selectAll(".bar").data(bins);

      peopleBar = peopleBar.enter().append("rect")
        .classed("person", true)
        .attr("x", d => panelX(d.x0) + 1)
        .attr("width", d => Math.max(0, panelX(d.x1) - panelX(d.x0) - 1))
        .attr("y", d => panelY(d.length))
        .attr("height", d => panelY(0) - panelY(d.length))
        .merge(peopleBar);

      peopleBar.exit().remove();


      xAxis = g => g
        .attr("transform", `translate(0,${height/4 - panelMargin.bottom})`)
        .call(d3.axisBottom(panelX).tickSizeOuter(0))
        .call(g => g.append("text")
            .attr("x", width - panelMargin.right)
            .attr("y", -4)
            .attr("fill", "#000")
            .attr("font-weight", "bold")
            .attr("text-anchor", "end")
            .text(data.x));

      yAxis = g => g
      .attr("transform", `translate(${panelMargin.left},0)`)
      .call(d3.axisLeft(panelY))
      .call(g => g.select(".domain").remove())
      .call(g => g.select(".tick:last-of-type text").clone()
          .attr("x", 4)
          .attr("text-anchor", "start")
          .attr("font-weight", "bold")
          .text(data.y));

      peopleGraph.append("g")
        .call(xAxis);

      peopleGraph.append("g")
          .call(yAxis);

      peopleGraph.append("g")
        // .append("text").text("Top Nodes by Degree:")
      .selectAll("text")
        .data(sortedData.slice(0,10))
        .enter().append("text")
          .text( (d, i) => {
            if (centralityType === "degree") {
              return `${i+1}. Name: ${d[1].name_variants}; Degree: ${d[1].local_degree}`;
            } else if (centralityType === "betweenness") {
              return `${i+1}. Name: ${d[1].name_variants}; Degree: ${d[1].local_betweenness}`;
            } else if (centralityType === "eigenvector") {
              return `${i+1}. Name: ${d[1].name_variants}; Degree: ${d[1].local_eigenvector}`;
            }
          })
          .attr("transform", (d,i) => { return `translate(0,${(height/4) + (i+1)*15})`})
          .classed("graph-text", true)
          .on("mouseover", function(d) {
            d3.select(this).attr("fill", "orange")
            d3.selectAll("circle.node").classed("transparent", true);
            d3.select(`#n${d[0]}`).classed("transparent", false);
          })
          .on("mouseout", function() {
            d3.select(this).attr("fill", "black")
            d3.selectAll("circle.node").classed("transparent", false);
            d3.selectAll(".link").classed("transparent", false);
          });
    })
  })
})


dispatch.on("load.textGraph", function() {

  var textGraph = svg.append('g')
          .classed("panel-container", true)
          .attr('width', width/3)
          .attr('height', height/4)
          .attr("transform", "translate(" + width * (2/3) +"," + height/2 + ")");

  textGraph.append("rect")
      .attr("width", "100%")
      .attr("height", height/2)
      .attr("fill", "#fff");

  dispatch.on("update.textGraph", function(graph, centralityType) {
    let projectedGraph = project(graph, 0);
    createNxGraph(projectedGraph, centralityType).then(sortedData => {

      let data = sortedData.map(s => s[1][`local_${centralityType}`]);

      panelX.domain(d3.extent(data));

      let bins = d3.histogram()
        .domain(panelX.domain())
        // .thresholds(20)
      (data)

      panelY.domain([0, d3.max(bins, d => d.length)])

      textGraph.selectAll("g").remove();

      var textG = textGraph.append("g");

      var textBar = textG.selectAll(".bar").data(bins);

      textBar = textBar.enter().append("rect")
        .classed("node", true)
        .attr("fill", d3.interpolateBlues(color(1575)))
        .attr("x", d => panelX(d.x0) + 1)
        .attr("width", d => Math.max(0, panelX(d.x1) - panelX(d.x0) - 1))
        .attr("y", d => panelY(d.length))
        .attr("height", d => panelY(0) - panelY(d.length))
        .merge(textBar);

      textBar.exit().remove();


      xAxis = g => g
        .attr("transform", `translate(0,${height/4 - panelMargin.bottom})`)
        .call(d3.axisBottom(panelX).tickSizeOuter(0))
        .call(g => g.append("text")
            .attr("x", width - panelMargin.right)
            .attr("y", -4)
            .attr("fill", "#000")
            .attr("font-weight", "bold")
            .attr("text-anchor", "end")
            .text(data.x));

      yAxis = g => g
      .attr("transform", `translate(${panelMargin.left},0)`)
      .call(d3.axisLeft(panelY))
      .call(g => g.select(".domain").remove())
      .call(g => g.select(".tick:last-of-type text").clone()
          .attr("x", 4)
          .attr("text-anchor", "start")
          .attr("font-weight", "bold")
          .text(data.y));

      textGraph.append("g")
        .call(xAxis);

      textGraph.append("g")
          .call(yAxis);

      textGraph.append("g")
        // .append("text").text("Top Nodes by Degree:")
      .selectAll("text")
        .data(sortedData.slice(0,10))
        .enter().append("text")
          .text( (d, i) => {
            if (centralityType === "degree") {
              return `${i+1}. Title: ${d[1].title}; Degree: ${d[1].local_degree}`;
            } else if (centralityType === "betweenness") {
              return `${i+1}. Title: ${d[1].title}; Degree: ${d[1].local_betweenness}`;
            } else if (centralityType === "eigenvector") {
              return `${i+1}. Title: ${d[1].title}; Degree: ${d[1].local_eigenvector}`;
            }
          })
          .attr("transform", (d,i) => { return `translate(0,${(height/4) + (i+1)*15})`})
          .classed("graph-text", true)
          .on("mouseover", function(d) {
            d3.select(this).attr("fill", d3.interpolateBlues(color(1575)) );
            d3.selectAll("circle.node").classed("transparent", true);
            d3.select(`#n${d[0]}`).classed("transparent", false);
          })
          .on("mouseout", function() {
            d3.select(this).attr("fill", "black");
            d3.selectAll("circle.node").classed("transparent", false);
          });
    })

  })
})


d3.json("all_eebo.json", function(error, origGraph) {
  if (error) throw error;

  dispatch.call("load", this);

  graph = {"nodes": origGraph.nodes, "links": correctDirection(origGraph.links)};
  createDateGraph(origGraph);
  origGraph = origGraph;

    var search = d3.select("#searchBox")
      .on('input', () => {
        let term = document.getElementById('searchBox').value;
        searchNodes(term);
      });

	// A pathDropdown menu with three different graph layouts (based on more limited subsets of nodes).
	var pathDropdown = d3.select('div#tools')
		.append('select')
		.on('change', function() {
			var val = this.value;
			if (val == "Bipartite (Texts and People)") {
				dispatch.call("update", this, currentGraph, centralityType);
			};
			if (val == "People Only") {
				var projectedPeopleGraph = project(currentGraph, 1);
        dispatch.call("update", this, projectedPeopleGraph, centralityType);
			};
			if (val == "Texts Only") {
				var projectedTextGraph = project(currentGraph, 0);
				dispatch.call("update", this, projectedTextGraph, centralityType);
			};

		});

	pathDropdown.selectAll('option')
		.data(['Bipartite (Texts and People)', 'People Only', 'Texts Only'])
		.enter().append('option')
		.attr('value', function(d) { return d; })
		.text(function(d) { return d; });

  var centralityDropdown = d3.select('div#tools')
		.append('select')
		.on('change', function() {
			var val = this.value;
			if (val == "Degree Centrality") {
				d3.select('#jesusCheckbox').attr('disabled', null);
        centralityType = "degree";
			};
			if (val == "Betweenness Centrality") {
				d3.select('#jesusCheckbox').attr('disabled', 'true');
        centralityType = "betweenness";
			};
			if (val == "Eigenvector Centrality") {
				d3.select('#jesusCheckbox').attr('disabled', 'true');
        centralityType = "eigenvector";
			};
      dispatch.call("update", this, currentGraph, centralityType);

		});

	centralityDropdown.selectAll('option')
		.data(['Degree Centrality', 'Betweenness Centrality', 'Eigenvector Centrality'])
		.enter().append('option')
		.attr('value', function(d) { return d; })
		.text(function(d) { return d; });

});

function project(thisGraph, bipartite) {
  // Get only nodes for one part of the graph
	var projectedNodes = thisGraph.nodes.filter( function(d) {return d.bipartite === bipartite;});

  const get_neighbors = (nodeId, links) => {
    neighbors = []
    links.forEach(l => {
      if (l.source.id === nodeId) {
        neighbors.push(l.target);
      } else if (l.target.id === nodeId) {
        neighbors.push(l.source);
      }
    });
    return neighbors
  }
	var projectedLinks = [];
  projectedNodes.forEach(function(n) {
    let nodeId = n.id;
    let neighbors1 = get_neighbors(nodeId, thisGraph.links);
    // console.log(neighbors1);
    let neighbors2 = neighbors1.map(n => get_neighbors(n.id, thisGraph.links));
    neighbors2 = [].concat(...neighbors2);
    neighbors2.forEach(neighbor => {
      projectedLinks.push({source: n, target:neighbor, weight:1});
    })
  });
	return {nodes:projectedNodes, links:projectedLinks};
}

const createNxGraph = (projectedGraph, centralityType) => {

  let nodes = projectedGraph.nodes.map(n => { return [n.id, n]; });
  let links = projectedGraph.links.map(l => { return [l.source.id, l.target.id, {'weight': l.weight, 'types': l.types, 'original_names': l.original_names}]})
  let G = new jsnx.Graph()
  G.addNodesFrom(nodes);
  G.addEdgesFrom(links);

  if (centralityType === "betweenness") {
    return new Promise ( (resolve, reject) => {
      jsnx.genBetweennessCentrality(G).then(betweenness => {
        jsnx.setNodeAttributes(G, 'local_betweenness', betweenness);
        let sortedData = G.nodes(true).sort((a,b) => d3.descending(a[1].local_betweenness, b[1].local_betweenness));
        resolve(sortedData);
      });
    })
  } else if (centralityType === "eigenvector") {
    return new Promise ( (resolve, reject) => {
      jsnx.genEigenvectorCentrality(G).then(eigenvector => {
        jsnx.setNodeAttributes(G, 'local_eigenvector', eigenvector);
        let sortedData = G.nodes(true).sort((a,b) => d3.descending(a[1].local_eigenvector, b[1].local_eigenvector));
        resolve(sortedData);
      });
    })
  } else if (centralityType === "degree") {
    let degree = G.degree();
    jsnx.setNodeAttributes(G, 'local_degree', degree);
    let sortedData = G.nodes(true).sort((a,b) => d3.descending(a[1].local_degree, b[1].local_degree));

    return new Promise( (resolve, reject) => {
      resolve(sortedData);
    })
  }

}

const filterDate = (graph,startDate,endDate) => {
  let newNodes = graph.nodes.filter(d => {
    if (startDate <= d.date && d.date <= endDate) {
      return d;
    }
  });
  let newNodeIds = newNodes.map(n => n.id);
  let newLinks = graph.links.filter(l => {
    if (newNodeIds.indexOf(l.source) !== -1 || newNodeIds.indexOf(l.target) !== -1) {
      return l;
    }
  });
  newLinks.forEach(l => {
    if (newNodeIds.indexOf(l.source) === -1) {
      newNodeIds.push(l.source)
    } else if (newNodeIds.indexOf(l.target) === -1) {
      newNodeIds.push(l.target)
    }
  });
  newNodes = graph.nodes.filter(d => newNodeIds.indexOf(d.id) !== -1);
  var newGraph = {nodes:newNodes, links:newLinks};
  return newGraph;
}

const searchNodes = term => {
  d3.selectAll("circle.node")
    .classed("transparent", d => {
      if ((d.name_variants && d.name_variants.indexOf(term) === -1) || (d.title && d.title.indexOf(term) === -1) || (d.author && d.author.indexOf(term) === -1)) {
        return true;}
      });
  d3.selectAll(".link").classed("transparent", true);
}

function countDateFrequency(origGraph) {
  // Same as above with dates
  var frequencies = {};
  origGraph.nodes.forEach(function(n) {
    if (n.date) {
      if (n.date in frequencies) {
        frequencies[n.date] += 1;
      } else {
        frequencies[n.date] = 1;
      }
    }
  });
  var data = [];
  for (var x in frequencies) {
    data.push({
      'year': x,
      'count': frequencies[x]
    });
  }
  return data;
}

function createDateGraph(origGraph) {
  // Same as above, for date range

  var dateData = countDateFrequency(origGraph);
  var dateGraph = svg.append('g')
          .classed("date-container", true)
          .attr('height', 70)
          .attr("transform", "translate(0," + height + ")");
  var dateMargin = {
      top: 0,
      right: 0,
      bottom: 10,
      left: 0
    },
    dateWidth = width - dateMargin.left - dateMargin.right,
    dateHeight = +dateGraph.attr("height") - dateMargin.top - dateMargin.bottom;

  var dateX = d3.scaleBand().range([4, dateWidth - 4]).padding(0.1),
    dateY = d3.scaleLinear().range([dateHeight, 15]);

  dateGraph.append("rect")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("fill", "#fff");

  var dateG = dateGraph.append("g");

  dateX.domain(dateData.map(function(d) {
    return d.year;
  }));
  dateY.domain([0, d3.max(dateData, function(d) {
    return d.count;
  })]);

  var dBrush = d3.brushX()
    .extent([
      [1, 10],
      [dateWidth, dateHeight]
    ])
    .handleSize(0)
    .on("brush", updateBrush)
    .on("end", brushed);

  let tens = dateX.domain().filter(d => { return d % 10 === 0;});

  dateG.append("g")
    .attr("class", "axis axis--x")
    .attr("transform", "translate(0," + dateHeight + ")")
    .call(d3.axisBottom(dateX).tickValues(tens).tickSize(0));

  dateG.selectAll(".bar")
    .data(dateData)
    .enter().append("rect")
    .attr("class", "bar")
    .attr("x", function(d) {
      return dateX(d.year);
    })
    .attr("y", function(d) {
      return dateY(d.count);
    })
    .attr("width", dateX.bandwidth())
    .attr("height", function(d) {
      return dateHeight - dateY(d.count);
    })
    .attr("fill", d => d3.interpolateBlues(color(d.year)));

  var dBrushSelection = dateG.append("g")
    .attr("class", "brush")
    .call(dBrush);

  //create custom handles
  dBrushSelection.selectAll(".handle-custom")
    .data([{
      type: "w"
    }, {
      type: "e"
    }])
    .enter().append("rect")
    .attr("class", function(d) {
      if (d.type === "e") {
        return "handle-custom handle-e";
      } else {
        return "handle-custom handle-w";
      }
    })
    .attr("width", 4)
    .attr("height", function(d) {
      return dateHeight / 2;
    })
    .attr("rx", 2)
    .attr("ry", 2)
    .attr("cursor", "ew-resize")
    .attr("x", function(d) {
      if (d.type === "e") {
        return dateWidth - 6;
      } else {
        return 2;
      }
    })
    .attr("y", function(d) {
      return dateHeight / 4 + 5;
    });

  //creates brush texts
  dBrushSelection.selectAll("brush-text")
    .data([{
      type: "w",
      year: 1590
    }, {
      type: "e",
      year: 1610
    }])
    .enter().append("text")
    .attr("class", function(d) {
      if (d.type === "e") {
        return "brush-text text-e";
      } else {
        return "brush-text text-w";
      }
    })
    .attr("text-anchor", function(d) {
      if (d.type === "e") {
        return "end";
      } else {
        return "start";
      }
    })
    .attr("x", function(d) {
      if (d.type === "e") {
        return dateWidth - 6;
      } else {
        return 2;
      }
    })
    .attr("y", 8)
    .text(function(d) {
      return d.year;
    });

  dBrushSelection.call(dBrush.move, [dateX(defaultStart),dateX(defaultEnd)]);

  function updateBrush() {
    var brushPositionX = d3.select(".date-container .selection").node().getBBox().x,
      brushPositionWidth = d3.select(".date-container .selection").node().getBBox().width;
    d3.select(".date-container .handle-custom.handle-w").attr("x", function(d) {
      return brushPositionX - 2;
    });
    d3.select(".date-container .handle-custom.handle-e").attr("x", function(d) {
      return brushPositionX + brushPositionWidth - 2;
    });

    var s = d3.event.selection || dateX.range();
    var convertDate = d3.scaleLinear().domain([0, dateWidth-4]).range([1500, 1700]);
    dateMin = Math.round(convertDate(s[0]));
    dateMax = Math.round(convertDate(s[1]));

    d3.select(".date-container .brush-text.text-w")
      .attr("x", function(d) {
        return brushPositionX - 2;
      })
      .attr("text-anchor", function(d) {
        if (dateMin < 1566 && (dateMax - dateMin) < 11) {
          return "start";
      } else if (dateMin >= 1566 && (dateMax - dateMin) < 11) {
          return "end";
        } else {
          return "start";
        }
      })
      .text(function(d) {
        return dateMin;
      });
    d3.select(".date-container .brush-text.text-e")
      .attr("x", function(d) {
        return brushPositionX + brushPositionWidth - 2;
      })
      .attr("text-anchor", function(d) {
        if (dateMax > 1700 && (dateMax - dateMin) < 11) {
          return "end";
        } else if (dateMax <= 1700 && (dateMax - dateMin) < 11) {
          return "start";
        } else {
          return "end";
        }
      })
      .text(function(d) {
        return dateMax;
      });
  }

  function brushed() {
    var s = d3.event.selection || dateX.range();
    var convertDate = d3.scaleLinear().domain([0, dateWidth-4]).range([1500, 1700]);
    dateMin = Math.round(convertDate(s[0]));
    dateMax = Math.round(convertDate(s[1]));

    currentGraph = filterDate(graph,dateMin,dateMax);
    dispatch.call("update", this, currentGraph, centralityType);
  }
}

const correctDirection = (links) => {
  let newLinks = links.map(l => {
    if (l.types.indexOf("signed") !== -1) {
      if (l.target.search(/^[A-Z]/) !== -1) {
        return l;
      } else {
        return {'source': l.target, 'target': l.source, 'weight': l.weight, 'types': l.types, 'original_names': l.original_names};
      }
    } else {
      if (l.source.search(/^[A-Z]/) !== -1) {
        return l
      } else {
        return {'source': l.target, 'target': l.source, 'weight': l.weight, 'types': l.types, 'original_names': l.original_names};
      }
    }
  });
  return newLinks;
}
