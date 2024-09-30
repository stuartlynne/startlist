
js = """
<script>
    
$(document).ready(function () {
    $("table").tablesorter({
        theme: 'default',   // Default theme with sorting arrows
        widgets: ['zebra'], // Zebra striping effect for the rows
    });
});


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

/* Reset the selection cell background color and hide the info and wave tables */
function resetSelection(selectionStr) {
    console.log('setSelection:', selectionStr);
    if (selectionStr === null) { return; }

    var selection = JSON.parse(selectionStr);
    console.log('setSelection:', selection);
    let [eventInfoCellId, infoTableId, waveTableAllId] = selection;
    console.log('resetSelection ID:', eventInfoCellId);
    console.log('resetSelection ID:', infoTableId);
    console.log('resetSelection ID:', waveTableAllId);
    clearBackgroundColor(eventInfoCellId);
    setDisplayInvisible(infoTableId);
    setDisplayInvisible(waveTableAllId);
}

/* Set the selection cell background color and show the info and wave tables */
function setSelection(selectionStr) {
    console.log('setSelection:', selectionStr);
    if (selectionStr === null) { return; }

    var selection = JSON.parse(selectionStr);
    console.log('setSelection:', selection);
    let [eventInfoCellId, infoTableId, waveTableAllId] = selection;
    console.log('setSelection Cell ID:', eventInfoCellId);
    console.log('setSelection Info ID:', infoTableId);
    console.log('setSelection Wave ID:', waveTableAllId);
    setBackgroundColor(eventInfoCellId, 'yellow');
    setDisplayVisible(infoTableId);
    setDisplayVisible(waveTableAllId);
}

var lastEventSelectionStr = null;
var lastWaveSelectionStr = null;

function toggleEventTable(toggleList ) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('toggleEventTable:', toggleList);
    newEventSelectionStr = toggleTableInternal(toggleList, lastEventSelectionStr);
    console.log('toggleEventTable: XXXX newEventSelectionStr:', newEventSelectionStr);
    if (newEventSelectionStr === null || newEventSelectionStr === '') { return; }

    resetSelection(lastEventSelectionStr);
    resetSelection(lastWaveSelectionStr);

    setSelection(newEventSelectionStr);
    lastEventSelectionStr = newEventSelectionStr;
    setCookie("eventSelection", lastEventSelectionStr, 7);  // Set new cookie

    waveSelection = [null, null, toggleList[2]];
    toggleWaveTable(waveSelection);
    lastWaveSelectionStr = JSON.stringify(waveSelection);
}

function toggleWaveTable(toggleList) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('toggleWaveTable:', toggleList);
    lastWaveSelectionStr = toggleTableInternal(toggleList, lastWaveSelectionStr);
    console.log('toggleWaveTable: lastWaveSelectionStr:', lastWaveSelectionStr);
    if (lastWaveSelectionStr === null || lastWaveSelectionStr === '') { return; }
    resetSelection(lastWaveSelectionStr);
    setSelection(lastWaveSelectionStr);
    lastWaveSelectionStr = lastWaveSelectionStr;
    setCookie("waveSelection", lastWaveSelectionStr, 7);  // Set new cookie
}

function toggleTableInternal(toggleList, lastSelectionStr ) {

    console.log('toggleTableInternal: toggleList:', toggleList);
    let [eventInfoCellId, infoTableId, waveTableAllId] = toggleList;
    console.log('toggleTable ID:', eventInfoCellId);
    console.log('toggleTable ID:', infoTableId);
    console.log('toggleTable ID:', waveTableAllId);

    let currentSelectionStr = JSON.stringify(toggleList);
    console.log('toggleTableInternal: current selection str:', currentSelectionStr);

    if (lastSelectionStr !== null && lastSelectionStr !== currentSelectionStr) {
        console.log('toggleEventTable: reset last selection:', lastSelectionStr);
        resetSelection(lastSelectionStr);
        lastSelectionStr = null;
    }
    return currentSelectionStr;
}

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
                console.log('searchBibNumber: interText:', bibCell.innerText);
            }
            if (bibCell.innerText === bibNumber) {
                console.log('searchBibNumber: %s found table: %s row: %d id: %s XXX', bibNumber, table.id, i, rows[i].id);
                foundFlag = true;
                rows[i].querySelectorAll('td').forEach(function(td) {
                    if (!setFlag) { 
                        setFlag = td.style.backgroundColor === 'white';
                    }
                    td.style.backgroundColor = setFlag ? highlightColor : 'white';
                });
            }
        }
    });
    console.log('searchBibNumber: foundFlag:', foundFlag);
    return foundFlag;
}

let bigHighlighted = [];
function toggleBib(bib) {
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



function setBackgroundColor(elementId, color) {
    let element = document.getElementById(elementId);
    if (element) {
        element.style.backgroundColor = color;
        console.log('setBackgroundColor:', elementId);
        return;
    }
    console.log('setBackgroundColor: element not found:', elementId);
}

function clearBackgroundColor(elementId) {
    let element = document.getElementById(elementId);
    if (element) {
        element.style.backgroundColor = '';
        console.log('clearBackgroundColor:', elementId);
        return;
    }
    console.log('clearBackgroundColor: element not found:', elementId);
}


function setDisplayVisible(elementId) {
    let element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'table';  // Or 'table' for table elements
        console.log('setDisplayVisible:', elementId);
        return;
    }
    console.log('setDisplayVisible: element not found:', elementId);
}

function setDisplayInvisible(elementId) {
    let element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
        console.log('setDisplayInvisible:', elementId);
        return;
    }
    console.log('setDisplayInvisible: element not found:', elementId);
}

function customAlert(message, timeout = 1400) {
    const alertBox = document.createElement('div');
    alertBox.textContent = message;
    alertBox.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        z-index: 9999;
    `;
    document.body.appendChild(alertBox);

    setTimeout(() => {
        alertBox.remove();
    }, timeout);
}

function setCookie(cname, cvalue, exdays) {
    console.log('setCookie: cname:', cname);
    const d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    let expires = "expires=" + d.toUTCString();
    //cookie = "lastSelectedCell=" + cvalue + ";" + expires + ";path=/";
    cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    console.log('setCookie: set cookie:', cookie);
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    let decodedCookie = decodeURIComponent(document.cookie);
    return "";
}
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    console.log('getCookie: decoded cookie:', decodedCookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            console.log('getCookie: %s: %s', cname, c.substring(name.length, c.length));
            return c.substring(name.length, c.length);
        }
    }
    console.log('getCookie: %s: null', cname);
    return "";
}

function reloadLast() {
    let lastPage = getCookie("lastPage");

    console.log('reloadLast: lastPage:', lastPage);

    let currentPage = window.location.pathname;
    console.log('reloadLast: currentPage:', currentPage);
    let lastModifiedDate = document.lastModified;
    console.log("Last Modified:" + lastModifiedDate);

    if (!lastPage || (lastPage !== currentPage)) {
        setCookie("lastPage", currentPage, 7);  // Set new cookie
        setCookie("eventSelection", '', 7);  // Set new cookie
        setCookie("lastBib", '', 7);  // Set new cookie
        return;
    }

    let eventSelectionStr = getCookie("eventSelection");
    let waveSelectionStr = getCookie("waveSelection");
    let lastBib = getCookie("lastBib");
    let bibHighlighted = getCookie("bibHighlighted");

    if (eventSelectionStr === "") { return; }

    var eventSelection = JSON.parse(eventSelectionStr);
    if (eventSelection === null) { return; }
    toggleEventTable(eventSelection);  // Restore last selected table if same page

    if (lastBib !== "") { 
        highlightBibNumber(lastBib, 'yellow', true); 
        lastBibNumber = lastBib;
        document.getElementById("bibInput").value = lastBib;
    }
    if (bibHighlighted !== "") {
        bigHighlighted = JSON.parse(bibHighlighted);
        console.log('reloadLast: bigHighlighted:', bigHighlighted);
        bigHighlighted.forEach(function(bib) {
            highlightBibNumber(bib, 'beige', true, true);
        });
    }
    if (waveSelectionStr === "") { return; }
    var waveSelection = JSON.parse(waveSelectionStr);
    if (waveSelection === null) { return; }
    toggleWaveTable(waveSelection);  // Restore last selected table if same page
}

window.onload = reloadLast;
</script>
"""
