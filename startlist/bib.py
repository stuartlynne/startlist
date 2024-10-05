bib = """

var lastBibNumber = null;
function highlightBibNumber(bibNumber, highlightColor, setFlag, debug = false) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    console.log('highlightBibNumber:', bibNumber, highlightColor, setFlag);

    if (!setFlag) {
        highlightColor = bibNumber in notesDictionary ? 'beige' : 'white'
    }

    selectors = `tr[id^="wtr_"][id$="_${bibNumber}"]`;
    console.log('highlightBibNumber: selectors: %s', selectors);
    trs = document.querySelectorAll(selectors);
    console.dir(trs);
    found = false;
    trs.forEach(tr => {
        found = true;
        console.log('highlightBibNumber: set tr: %s', tr.id);    
        tr.style.backgroundColor = highlightColor;
        if(!(bibNumber in namesDictionary)) {
            //var tr = event.target.closest('tr');
            //tr = tr.previousElementSibling;
            //console.log('HNKD: tr:', tr.id);
            var tds = tr.querySelectorAll('td');
            var name = tds[3].innerText;
            namesDictionary[bibNumber] = name;
            console.log('HNKD: added name:', name);
        }
    });

    // get name into namesDictionary

        
    return found;

}

/* toggleBib */
function TB(bib, noteId) {
    console.log('toggleBib: bib: %s noteId: %s', bib, noteId);
    if (noteId) {
        toggleNoteRow(bib, noteId);
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
    var bibNumber = document.getElementById("bibInput").value;
    console.log('heandleKeyDown: %s', bibNumber);
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
    console.log('searchBibNumber: bib: %s lastBib: %s', bibNumber, lastBibNumber);

    if (!bibNumber || bibNumber === "") {
        if (!lastBibNumber) { return; }
        highlightBibNumber(lastBibNumber, null, false);
    }
    if (bibNumber === lastBibNumber) { return; }

    if (lastBibNumber) {
        highlightBibNumber(lastBibNumber, 'yellow', false);
        lastBibNumber = null;
    }

    if (highlightBibNumber(bibNumber, 'yellow', true) === true) {
        lastBibNumber = bibNumber;
        setCookie("lastBib", bibNumber, 7);  // Set new cookie
        return;
    }
    //customAlert("Bib number not found. XXX");
    lastBibNumber = null;

}
"""
