bib = """

/* highlightBibNumber 
 * Highlight the bib number in the table.
 * This is used to highlight the bib number in the table when the bib number is entered 
 * in the input field and when there is a note associated with the bib number.
 *
 * N.B. each bib number is present in two tables. The event all waves table and the wave 
 * specific table.
 */

var lastBibNumber = null;
function highlightBibNumber(bibNumber, highlightColor, setFlag, debug = false) {
    if (!setFlag) {
        highlightColor = bibNumber in notesDictionary ? 'beige' : 'white'
    }

    selectors = `tr[id^="wtr_"][id$="_${bibNumber}"]`;
    trs = document.querySelectorAll(selectors);
    found = false;
    trs.forEach(tr => {
        found = true;
        tr.style.backgroundColor = highlightColor;
        if(!(bibNumber in namesDictionary)) {
            var tds = tr.querySelectorAll('td');
            var name = tds[3].innerText;
            namesDictionary[bibNumber] = name;
        }
    });
    return found;
}

/* toggleBib */
function TB(bib, noteId) {
    if (noteId) {
        toggleNoteRow(bib, noteId);
    }
}

// Ensure only numbers are inputted
function isNumber(evt) {
    var charCode = (evt.which) ? evt.which : evt.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57))
        return false;
    return true;
}
// handle keydown event
function handleKeyDown(evt) {
    var bibNumber = document.getElementById("bibInput").value;
    if (evt.key === 'Enter') {
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
