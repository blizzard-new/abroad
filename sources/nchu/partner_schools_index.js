$(document).ready(function(){
    var sltMenusNames = []; //create array to hold dropdown menus' names for later populating
    sltMenusNames[0] = "sltContinentTW";
    sltMenusNames[1] = "sltContinentEN";
    sltMenusNames[2] = "sltCountryTW";
    sltMenusNames[3] = "sltCountryEN";
    sltMenusNames[4] = "sltOverseasInsitutionTW";
    sltMenusNames[5] = "sltOverseasInsitutionEN";
    sltMenusNames[6] = "sltCooperativeProgramTW";
    sltMenusNames[7] = "sltCooperativeProgramEN";
    sltMenusNames[8] = "sltLocalInsitutionTW";
    sltMenusNames[9] = "sltLocalInsitutionEN";
    sltMenusNames[10] = "sltDate";

    var queryStrings = ["","","","","","","","","","",""]; //create array to hold the strings user chooses to show in table

    $('#btnLoad').click(function(){
        queryStrings = ["","","","","","","","","","",""]; //clear array

        $("[id^=slt]").each(function(){ //clear the dropdown menus when button clicked or you get repeats
            $(this).empty();
            $('<option/>').val("").html("").appendTo(this);
        });

        $.ajax({
            url:"OIA_data.csv",
            dataType:"text",
            success:function(data)
            {
                data = data.replace(/[[\]{}()*+?\r\"\'\^$|#]/g, " ");//remove any special characters
                var OIA_data = data.split(/\r?\n/); //split the rows
                var table_data = '<table class="table table-bordered table-striped">';
                for(var rowCount = 0; rowCount < OIA_data.length; rowCount++){
                    var cell_data = OIA_data[rowCount].split(","); //split on comma
                    table_data += '<tr>';
                    for(var cell_count = 0; cell_count < cell_data.length;
                        cell_count++)
                        {
                            if(rowCount === 0){ //special case for header row
                                if (cell_count%2 == 0 && cell_count < 10){ //if column number is even and NOT the last two columns
                                    table_data += '<th class="TW">'+cell_data[cell_count]+ '</th>';
                                }else if(cell_count < 10){
                                    table_data += '<th class="EN">'+cell_data[cell_count]+ '</th>';
                                }else if(cell_count == 10){
                                    table_data += '<th class="ENdate">'+cell_data[cell_count]+ '</th>'; //no language so NO class                              
                                }else if(cell_count == 11){
                                    table_data += '<th class="ENlink">'+cell_data[cell_count]+ '</th>'; //no language so NO class                              
                                } //end if/else even column
                            }else{
                                if (cell_count%2 == 0 && cell_count < 10){ //if column number is even and NOT the last two columns
                                    table_data += '<td class="TW">'+cell_data[cell_count]+ '</td>';
                                }else if(cell_count < 10){
                                    table_data += '<td class="EN">'+cell_data[cell_count]+ '</td>';
                                }else{ //just no language so NO class
                                    if(cell_count == 11){ //the last column is URL so make into hyperlink
                                        table_data += '<td><a href="'+cell_data[cell_count]+ '" target="_blank" class="hyperlink">Webpage</a></td>';
                                    }else{
                                        table_data += '<td>'+cell_data[cell_count]+ '</td>'; 
                                    } //end if
                                } //end if/else even column
                            }
                        }
                        table_data += '</tr>';
                }
                table_data += '</table>';
                $('#tblList').html(table_data);

                var oiaSingleColumnData = []; //single dimensional array to hold single columns
                var oiaAllColumnData = []; //multidimensional array to hold all single columns arrays
                var numberOfColumns = OIA_data[0].split(",").length; //get the number of columns in FIRST row
                var OIA_data = data.split(/[\n\r,]/); //split all data on commas & new lines
                var DataLength = OIA_data.length; //total records in data

                for(var allColumns = 0; allColumns < numberOfColumns; allColumns ++){ 
                    //start after heading row and jump every number of columns to get SAME column's next value
                    oiaAllColumnData[allColumns] = "";
                    for(var columnCount = numberOfColumns + allColumns; columnCount < DataLength - 1; columnCount += numberOfColumns){ 
                            oiaAllColumnData[allColumns] += OIA_data[columnCount];
                            oiaAllColumnData[allColumns] += ",";                            
                        //i ++ ;
                    } //for loop one column
                    oiaAllColumnData[allColumns] = oiaAllColumnData[allColumns].split(","); //insert array into array
                    oiaAllColumnData[allColumns] = [...new Set(oiaAllColumnData[allColumns])]; //remove repeats
                } //for loop all columns
                var options = "";
                for(var j = 0; j < sltMenusNames.length; j++){
                    for(var i = 0; i < oiaAllColumnData[j].length; i++){
                        if(oiaAllColumnData[j][i] != ''){ //remove empties then append the value to the sltmenu
                            if(j%2 == 0){ //if Even, i.e., Chinese
                                $('<option/>').val(oiaAllColumnData[j+1][i]).html(oiaAllColumnData[j][i]).appendTo('#'+sltMenusNames[j]);
                            }else{
                                $('<option/>').val(oiaAllColumnData[j-1][i]).html(oiaAllColumnData[j][i]).appendTo('#'+sltMenusNames[j]);                                
                            }
                        }//end if
                    }//end for
                }//end for

                //alpha order slt menus
                for(var j = 0; j < sltMenusNames.length; j++){
                    var sltMenuToOrder = sltMenusNames[j];
                    $("#" + sltMenuToOrder).html($("#" + sltMenuToOrder + " option").sort(function(x, y) {
                        return $(x).text() < $(y).text() ? -1 : 1;
                    }))
                    $("#" + sltMenuToOrder).get(0).selectedIndex = 0;
                };//end for alpha order slt menus

                //testing language on live page (fix later to use the URL to grab current language)
                var pageLanguage = (window.location.href)
                pageLanguage = pageLanguage.substring(pageLanguage.length - 2);
                if(pageLanguage == "en"){
                    setTimeout(function (){
                        $("#btnLanguageEN").click(); //fire button to English
                        $(".ENdate").html("Signing Date");
                        $(".ENlink").html("Visit Website");
                    }, 100);
                }else{
                    setTimeout(function (){
                        $("#btnLanguageTW").click(); //fire button to Chinese
                        $(".ENdate").html("簽約年份");
                        $(".ENlink").html("學校網址");
                    }, 100);
                }
                
//console.log("#of menus:" + sltMenusNames.length)
//console.log("columns: "+numberOfColumns);
//console.log("rowCount: "+ rowCount);
//console.log(DataLength);
//console.table(oiaAllColumnData);
//console.log(queryStrings);

            } //data success function
        }); //ajax function
    }); //btn function

    $("[id^=slt]").change(function(){
        //change the other language sltMenu to match the current choice
        var changedLanguage = this.id.substr(this.id.length - 2); //get the language of sltMenu just changed
        var changedMenu = this.id.substr(0, this.id.length - 2); //get the name of the sltMenu just changed
        var searchType = $("input[type='radio'].radioBtnClass:checked").val();
        var searchTypeAnd = 0; //remember if row has a single NOT match to KEEP hidden
        if (changedLanguage == "TW"){ //if Chinese so update EN
            $("#" + changedMenu + "EN").val($(this).find("option:selected").text());
        }else if(changedLanguage == "EN"){ //if English so update CN
            $("#" + changedMenu + "TW").val($(this).find("option:selected").text());
        }else{ //date do no language to change
            //do nothing
        } //end if/else even column

        //rebuild query string for both TW and EN
        for(var i = 0; i < queryStrings.length; i++){
            queryStrings[i] = $("#" + sltMenusNames[i]).find("option:selected").text(); //get the current values of sltMenus
        } //end if

        //Hide all rows again before filtering again
        $("#tblList tr:gt(0)").each(function(){ //:gt(0) skips the header row
            if(searchType == 0){ //user chooses AND so work back from show TO hide
                $(this).show();
            }else{
                $(this).hide(); //user choose OR so work back from hide to show
            } //end if
        }); //end function

        searchTypeAnd = 0; //setup the variable to show a NON-MATCH will cancel the whole row from being shown            
        for(var i = 0; i < queryStrings.length; i++){ //run through filter array looking for match in each table row
            //Declare using class, useful for build a RegExp from a variable
            var strShow = queryStrings[i];

            if(strShow !==""){
                $("#tblList tr:gt(0)").each(function(){ //:gt(0) skips the header row
                //AND no match once faded out NEVER fades back in
                //OR once faded in NEVER fades back out                    
                    if($(this).text().match(new RegExp(strShow, 'gi'))){ //if a match, SHOW the row
                        //alert(strShow);image.png
                        //$(this).fadeIn();
                        if(searchType == 1){ //the user choose OR radio button
                            $(this).fadeIn();
                        } //end if
                    }else{
                        if(searchType == 0){ //the user choose AND radio button so TURN OFF any NON-matching
                            $(this).fadeOut(); //if no match, HIDE the row
                            //searchTypeAnd = 1; //keep it faded out for the AND option
                        }//end if
                    }; //end if
                }); //end function
            } //end if //end if not empty string
        } //end for
    }); //end sltMenu changed

$("#btnLanguageTW").click(function(){
//change the filter strings to match the new language EN TO TW
    $("#btnLanguageTW").html("中文"); //change button language
    $("#btnLanguageEN").html("英文"); //change button language   
    $("#btnLoad").html("清除"); //change button language   
    $(".hyperlink").html("前往學校網站");
    $("#txtMainTitle").html("姊妹校清單"); //change txt heading language
    $("#txtFilterTitle").html("篩選條件"); //change txt heading language
    setTimeout(function (){
        $(".ENdate").html("簽約年份");
        $(".ENlink").html("學校網址");
    }, 100);
    $(".TW").show();
    $(".EN").hide();

});

$("#btnLanguageEN").click(function(){
//change the filter strings to match the new language TW to EN
    $("#btnLanguageTW").html("Chinese"); //change button language
    $("#btnLanguageEN").html("English"); //change button language    
    $("#btnLoad").html("Reset"); //change button language   
    $(".hyperlink").html("Visit Website");
    $("#txtMainTitle").html("Partner Institution Listings"); //change txt heading language
    $("#txtFilterTitle").html("Filter List"); //change txt heading language
    setTimeout(function (){
        $(".ENdate").html("Signing Year");
        $(".ENlink").html("Visit Website");
    }, 100);
    $(".TW").hide();
    $(".EN").show();
});

$("[id^=rdo]").click(function(){
//    alert($("input[type='radio'].radioBtnClass:checked").val());
});

$("#btnLoad").click(); //fire button on page load

}); //document ready function
