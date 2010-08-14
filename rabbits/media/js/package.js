google.load("visualization", "1", {packages:["imagesparkline"]});
google.setOnLoadCallback(drawChart);

function make(data) {
    data.setValue(0,0,Math.random()*100+1);
    data.setValue(1,0,Math.random()*100+1);
    data.setValue(2,0,Math.random()*100+1);
    data.setValue(3,0,Math.random()*100+1);
    data.setValue(4,0,Math.random()*100+1);
    data.setValue(5,0,Math.random()*100+1);
    data.setValue(6,0,Math.random()*100+1);
    data.setValue(7,0,Math.random()*100+1);
    data.setValue(8,0,Math.random()*100+1);
    data.setValue(9,0,Math.random()*100+1);
    
    return data;
};

function drawChart() {
  var data = new google.visualization.DataTable();
  data.addColumn("number", "Commit History");
  data.addRows(10);

  data = make(data);
//  var chart = new google.visualization.ImageSparkLine(document.getElementById('package-githubcommits'));
  chart.draw(data, {width: 120, height: 40, showAxisLines: false,  showValueLabels: false, labelPosition: 'left'});
}

