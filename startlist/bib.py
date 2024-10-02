bib = """

var lastBibNumber = null;
function highlightBibNumber(bibNumber, highlightColor, setFlag, debug = false) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('highlightBibNumber:', bibNumber, highlightColor, setFlag);
    var found = false;
    var allTables = document.querySelectorAll('table[id*="_wave_"]');
    foundFlag = false;
    allTables.forEach(function(table) {
        console.log('searchBibNumber: table:', table.id);
        var rows = table.getElementsByTagName('tr');
        for (var i = 1; i < rows.length; i++) {  // Skip header row
            index = (table.id.endsWith('_wave_all')) ? 1 : 0; 
            var bibCell = rows[i].getElementsByTagName('td')[index];  // Assuming Bib is in the first column
            if (!bibCell || !bibCell.innerText || bibCell.innerText === "") { continue; }
            if (debug) {
                console.log('searchBibNumber: innerText:', bibCell.innerText);
            }
            if (bibCell.innerText === bibNumber) {
                console.log('searchBibNumber: %s found table: %s row: %d id: %s XXX', bibNumber, table.id, i, rows[i].id);
                foundFlag = true;
                rows[i].querySelectorAll('td').forEach(function(td) {
                    if (!setFlag) { setFlag = td.style.backgroundColor === 'white'; }
                    td.style.backgroundColor = setFlag ? highlightColor : 'white';
                });
            }
        }
    });
    console.log('searchBibNumber: foundFlag:', foundFlag);
    return foundFlag;
}

let bigHighlighted = [];
function toggleBib(bibId) {
    toggleNoteRow(bibId);
    console.log('toggleBib:', bib);
    if (bib) {
        if (bigHighlighted.includes(bib)) {
            bigHighlighted = bigHighlighted.filter(item => item !== bib);
            highlightBibNumber(bib, 'beige', false, true);
        } else {
            bigHighlighted.push(bib);
            highlightBibNumber(bib, 'beige', true, true);
        }
        setCookie("bibHighlighted", JSON.stringify(bigHighlighted), 7);  // Set new cookie
    }
}



// Ensure only numbers are inputted
function isNumber(evt) {
    console.log('isNumber: %s', evt.which);
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57))
        return false;
    return true;
}
// handle keydown event
function handleKeyDown(evt) {
    console.log('heandleKeyDown: %s', evt.which);
    if (evt.key === 'Enter') {
        console.log('heandleKeyDown: Enter');
        searchBibNumber(false);
    }
}


function clearInput() {
    document.getElementById('bibInput').value = '';
    highlightBibNumber(lastBibNumber, 'yellow', false);
    lastBibNumber = null;
    setCookie("lastBib", '', 7);  // Set new cookie
}

var lastBibNumber = null;
function searchBibNumber(reset) {
    var bibNumber = document.getElementById("bibInput").value;
    console.log('Searching for bib number:', bibNumber);

    if (!bibNumber || bibNumber === "") {
        if (!lastBibNumber) { return; }
        highlightBibNumber(lastBibNumber, 'yellow', false);
    }
    if (bibNumber === lastBibNumber) { return; }

    highlightBibNumber(lastBibNumber, 'yellow', false);
    if (highlightBibNumber(bibNumber, 'yellow', true) === true) {
        lastBibNumber = bibNumber;
        setCookie("lastBib", bibNumber, 7);  // Set new cookie
        return;
    }
    //customAlert("Bib number not found. XXX");
    lastBibNumber = null;

}
"""
