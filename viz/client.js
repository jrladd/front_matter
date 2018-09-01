var node,link,newGraph;

// instantiate the scrollama
const scroller = scrollama();

// setup the instance, pass callback functions
scroller
  .setup({
    step: '.step', // required
    container: '.scrolly'
  })
  .onStepEnter(handleStepEnter)
  .onStepExit(handleStepExit);
  // .onContainerExit(handleContainerExit);

function handleStepEnter(response) {
  let $step = response.element.dataset.step;
  if ($step === "start") {
    simulation.force("charge", d3.forceManyBody().distanceMax([100]))
    updateGraph(startingGraph);
  } else if ($step === "add-edges") {
    newGraph = addEdges(startingGraph);
    simulation.force("charge", d3.forceManyBody().strength([-3000]))
    updateGraph(newGraph);
  } else if ($step === "recolor") {
    updateGraph(newGraph);
    node.classed("person", d => { if (d.bipartite === 1) {return false} else {return true;}})
      .attr("fill", d => {if (d.bipartite === 1) { return "lightblue"; }});
  } else if ($step === "add-arrows") {
    updateGraph(newGraph);
    node.classed("person", d => { if (d.bipartite === 1) {return false} else {return true;}})
      .attr("fill", d => {if (d.bipartite === 1) { return "lightblue"; }});
    link.attr("marker-end", "url(#tutorial-arrow)");
  } else if ($step === "project-people") {
    updateGraph(newGraph);
    let projectedPeopleGraph = project(newGraph, 0);
    updateGraph(projectedPeopleGraph);
  } else if ($step === "project-text") {
    updateGraph(newGraph);
    node.classed("person", d => { if (d.bipartite === 1) {return false} else {return true;}})
      .attr("fill", d => {if (d.bipartite === 1) { return "lightblue"; }});
    let projectedTextGraph = project(newGraph, 1);
    updateGraph(projectedTextGraph);
  } else if ($step === "color-scale") {
    updateGraph(newGraph);
    link.attr("marker-end", "url(#tutorial-arrow)");
    node.attr("fill", d => {if (d.bipartite === 1) { return d3.interpolateBlues(color(d.year)); } });
  }
  console.log("handling scroll", response.element.dataset.step);
  // $graph.classed("bg-green", true).text("Hello "+(response.index+1));
}

function handleStepExit(response) {
  // console.log("done with step", response.index);
}

// function handleContainerExit(response) {
//   console.log('scroll done!');
// }

var svg = d3.select("#tutorial")
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 500 500")
    .classed("svg-content-responsive", true);

var width = +svg.attr("width")+800;
    height = +svg.attr("height")+500;

var color = d3.scaleLinear()
	.domain([1500,1700])
	.range([0.1,1]);

svg.append('rect')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('fill', '#F4F4F4')
    .on("click", () => {
      node.classed("transparent", false);
      link.classed("transparent", false);
    });

svg.append("defs").append("marker")
    .attr("id", "tutorial-arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 45)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
  .append("path")
    .attr("d", "M0,-5L10,0L0,5");

var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function(d) { return d.id; }).iterations(2))
    .force("charge", d3.forceManyBody().strength([-200]))
    .force("center", d3.forceCenter(width / 3, height / 2))
    .force("collide", d3.forceCollide().iterations(0));


var container = svg.append('g');
link = container.append('g').selectAll('.link');
node = container.append('g').selectAll('.node');

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

const startingGraph = {nodes: [{"id": 1, bipartite: 0}, {"id": 2, bipartite: 1, year: 1550}, {"id": 3, bipartite: 0}, {"id": 4, bipartite: 1, year: 1650}, {"id": 5, bipartite: 0}], links: []}

const addEdges = (graph) => {
  let nodes = graph.nodes;
  let links = [
    {source:1,target:2},
    {source:2,target:3},
    {source:3,target:4},
    {source:4,target:5},
    {source:4,target:1},
    {source:2,target:5}
  ]
  return {nodes:nodes,links:links}
}
const updateGraph = (graph) => {
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
      // .attr("marker-end", "url(#arrow)")
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
    .attr('r', 20)//function(d, i) {if (d.bipartite === 1) {return degreeSize(d.degree);} else {return 8;} })
    // Color by degree centrality calculation in NetworkX.
      .attr("fill", function(d) {if (d.bipartite === 0) {return d3.interpolateBlues(color(d.date));} })
      .attr('class', 'node')
      .classed('person', true)//d => { if (d.bipartite === 1) {return true; } })
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
}

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
