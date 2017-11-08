var apiUrl = location.protocol + '//' + location.host + location.pathname + "api/";
var AjaxResponse = {};
$('#show_analytics').click(function() {
    $("#analytics").toggle();
  });

$('#downloadtoCSV').click(function() {
    JSONToCSV(AjaxResponse,true);
  });
//Populate Analytics Selector
$("#analytics").hide();

$("#portfolio_file").change(function(e) {
 // The event listener for the file upload
    var ext = $("input#portfolio_file").val().split(".").pop().toLowerCase();
    $('.sandboxtwo').toggleClass('loading');
    $('.loader').addClass('active');
    if($.inArray(ext, ["csv"]) == -1) {
        alert('Upload CSV');
        return false;
    }   
    if (e.target.files != undefined) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var csvval=e.target.result.split("\n");
            var json_file = JSON.stringify(csvval);
            $.ajax({
                type: 'POST',
                url: apiUrl + 'upload',
                data: json_file,
                dataType: 'json',
                contentType: 'application/json',
                success: function(data) {
                    console.log(data);
                    alert("Portfolio uploaded successfully.");
                    window.location = window.location;
                }
            });
        };
    reader.readAsText(e.target.files.item(0));
    }  
    return false;
});
//check user input and process, generate result in tables
$('.run-analysis.Button').click(function(){
    var Portfolio = $('.enter-portfolio select').find(":selected").text();
    var Portfolio = JSON.stringify(Portfolio);
    var selected = [];                
    $("input:checkbox[name=analytics]:checked").each(function() {
           selected.push($(this).val());
    });
    input_parameters = {};
    input_parameters["portfolio"] = Portfolio.replace(/"/g,"");
    input_parameters["analytics"] = selected;
    input_parameters = JSON.stringify(input_parameters);
    console.log(Portfolio)
    //verify input otherwise display an informative message
    if(Portfolio.includes('Loading...')) {
        alert("Load a portfolio first using Investment Portfolio service");
        return;
      } else if(Portfolio.includes('[pick portfolio]')) {
        alert("Select a portfolio");
        return;
      }
      $('.sandboxtwo').toggleClass('loading');
      $('.loader').addClass('active');
      $.ajax({
        type: 'POST',
        url: apiUrl + 'unit_test',
        data: input_parameters,
        dataType: 'json',
        contentType: 'application/json',
        success: function(data,input_parameters) {
            console.log(data);
            if ($("input[name='download_or_here']:checked").val() == "download"){
                JSONToCSV(data,true)
                $('.sandboxtwo').removeClass('loading');
                $('.loader').removeClass('active');
            }else{
                $('.sandboxtwo').removeClass('loading');
                $('.sandboxtwo').addClass('analysis');
                $('.loader').removeClass('active');
                AjaxResponse = data;
                Process(data,function(){}); //Execute Process Function to update the UI with results.
            }
        }
    });
});

//create the output tables
function Process(data) {
    //process input into server to create output json
    //display today's date
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth()+1;
    var yyyy = today.getFullYear();
    if(dd<10) {
        dd='0'+dd
    }
    if(mm<10) {
        mm='0'+mm
    }
    today = mm+'/'+dd+'/'+yyyy;
    $('.date a').text(today);

    //update header
    var holdings_title = 'Portfolio analytics results:';
    $('.title1 h3').text(holdings_title);
    th = '<tr style="width: 100%"><th>Name</th><th>ID</th><th>Quantity</th>'
    for (var key in data[0]){
        if(['name','quantity','id','portfolio','date'].includes(key) == false){
            th += "<th>" + AnalyticName(key) + "</th>";
        }
    }
    th += "</tr>"
    $('.port-table thead').html(th);

    //display holdings data
    var holdingsDataLength = data.length;
    var tr = "";
    for (var i = 0; i < holdingsDataLength; i++) {
        var name = data[i].name;
        var identifier = data[i].id;
        var quantity = data[i].quantity;
        //create row in table
        tr += "<tr tabindex='0' aria-label=" + name + "><td>" + name + "</td><td>" + identifier + "</td><td>" + quantity + "</td>";
        for (var key in data[i]){
            if(['name','quantity','id','portfolio','date'].includes(key) == false){
                tr += "<td>" + data[i][key] + "</td>";
            }
        }
        tr += "</tr>"
    }
    $('.port-table tbody').html(tr);
}

//sort the objects on key
function sortByKey(array, key) {
    return array.sort(function(a, b) {
        var x = a[key]; var y = b[key];
        return ((x > y) ? -1 : ((x < y) ? 1 : 0));
    });
}
function AnalyticName(analytic){
    var text = "";
    switch (analytic) {
        case "THEO/Price":
            text = "Price (Clean Price)";
            break
        case "THEO/Value":
            text = "Value (Dirty Price)";
            break
        case "THEO/Exposure":
            text = "Exposure";
            break
        case "THEO/Accrued Interest":
            text = "Accrued Interest";
            break
        case "THEO/Yield":
            text = "Yield";
            break   
        case "THEO/Macaulay Duration":
            text = "Macaulay Duration";
            break             
        case "THEO/Adjusted Duration":
            text = "Adjusted Duration";
            break
        case "THEO/Effective Duration":
            text = "Effective Duration";
            break
        case "THEO/Adjusted Duration2":
            text = "Spread Duration";
            break
        case "THEO/Effective Convexity":
            text = "Effective Convexity";
            break
        case "THEO/Delta":
            text = "Delta";
            break
        case "THEO/Gamma":
            text = "Gamma";
            break
        case "THEO/Domestic Rho":
            text = "Domestic Rho";
            break
        case "THEO/Theta":
            text = "Theta";
            break
        case "THEO/Vega":
            text = "Vega";
            break                             
        default: 
            text = analytic;
    }
    return text;
}
//source: http://jsfiddle.net/hybrid13i/JXrwM/
function JSONToCSV(JSONData, ShowLabel) {
    //If JSONData is not an object then JSON.parse will parse the JSON string in an Object
    var arrData = typeof JSONData != 'object' ? JSON.parse(JSONData) : JSONData;
    var CSV = '';    
    //This condition will generate the Label/Header
    if (ShowLabel) {
        var row = "";   
        //This loop will extract the label from 1st index of on array
        for (var index in arrData[0]) {
            //Now convert each value to string and comma-seprated
            row += index + ',';
        }
        row = row.slice(0, -1);
        //append Label row with line break
        CSV += row + '\r\n';
    }
    //1st loop is to extract each row
    for (var i = 0; i < arrData.length; i++) {
        var row = "";
        //2nd loop will extract each column and convert it in string comma-seprated
        for (var index in arrData[i]) {
            row += '"' + arrData[i][index] + '",';
        }
        row.slice(0, row.length - 1);
        //add a line break after each row
        CSV += row + '\r\n';
    }
    if (CSV == '') {        
        alert("Invalid data");
        return;
    }   
    
    //Generate a file name
    var portfolioName = $("#portfolio_name :selected").text();
    var fileName = "PortfolioAnalytics_" + portfolioName.replace(/ /g,"_");
    //this will remove the blank-spaces from the title and replace it with an underscore
    
    //Initialize file format you want csv or xls
    var uri = 'data:text/csv;charset=utf-8,' + escape(CSV); 
    
    //this trick will generate a temp <a /> tag
    var link = document.createElement("a");    
    link.href = uri;
    
    //set the visibility hidden so it will not effect on your web-layout
    link.style = "visibility:hidden";
    link.download = fileName + ".csv";
    
    //this part will append the anchor tag and remove it after automatic click
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
