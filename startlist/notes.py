notes = """
var notesDictionary = {};  // Dictionary to store notes keyed by bib number
var namesDictionary = {};  // Dictionary to store names keyed by bib number

//var lastBibNumber = null;
function openNoteBib(bibNumber, setFlag, debug = false) {
    var found = false;
    var allTables = document.querySelectorAll('table[id*="_wave_"]');
    foundFlag = false;
    allTables.forEach(function(table) {
        var rows = table.getElementsByTagName('tr');
        for (var i = 1; i < rows.length; i++) {  // Skip header row
            index = (table.id.endsWith('_wave_all')) ? 1 : 0; 
            var bibCell = rows[i].getElementsByTagName('td')[index];  // Assuming Bib is in the first column
            if (!bibCell || !bibCell.innerText || bibCell.innerText === "") { continue; }
        }
    });
    return foundFlag;
}

// Toggle visibility of the note row
function toggleNoteRow(bib, noteId) {
    var noteRow = document.getElementById(noteId);

   // Find the input field inside the row
    var inputField = noteRow.querySelector('input.note-input');

    // Set the placeholder dynamically if it hasn't been set yet
    if (inputField && !inputField.placeholder) {
        inputField.placeholder = `Competition note for ${bib}`;
    }

    if (noteRow.style.display === 'none' || noteRow.style.display === '') {
        noteRow.style.display = 'table-row';
    } else {
        noteRow.style.display = 'none';
    }
}

/* Handle keydown event 
 * The event handler keeps the note data in sync with the input field,
 * The inputId is the other input field for this bib number.
 */
function HNKD(event, bib, inputId) {

    noteValue = event.target.value.trim();
    notesDictionary[bib] = noteValue;
    setCookie('notesDictionary', JSON.stringify(notesDictionary), 7);  // Save the notes to a cookie

    // Update the other input field with the same note value
    var noteInput = document.getElementById(inputId);
    noteInput.value = noteValue

    // Highlight the bib number
    if (bib != lastBibNumber) {
        highlightBibNumber(bib, 'beige', noteInput.value.trim().length, true);  // Highlight the bib number
    }

}

function downloadNotes(event, date) {
    notesData = "# Competition Notes: " + event + "\\n";
    notesData += "# Date: " + date + "\\n\\n";
    notesData += "### Saved: " + getCurrentDateTime() + "\\n";

    Object.keys(notesDictionary).forEach(function(bib) {
        notesData += "\\n---\\n";
        notesData += "### Bib: " + bib + " " + namesDictionary[bib] + "\\n";
        notesData += notesDictionary[bib] + "\\n";
    });

    let filename = date + '_' + event + '_notes';
    const blob = new Blob([notesData], { type: 'text/plain' });
    const file = new File([blob], filename+'.md', { type: 'text/plain' });

    if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({
            title: filename,
            files: [file]
        }).then(() => {
            console.log('Shared successfully');
        }).catch((error) => {
            console.error('Error sharing:', error);
        });
        customAlert("Shared: " + filename, 1000);
    } else {
        customAlert("Sharing not supported, download.", 5000);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename+'.md';  // Set file name
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

function restoreNotes() {

    for (const bib in notesDictionary) {
        if (notesDictionary[bib] === "") { continue; }
        const selectors = `input[id^="wti_"][id$="_${bib}"]`;
        const noteInputs = document.querySelectorAll(selectors);
        if (bib != lastBibNumber) {
            highlightBibNumber(bib, 'beige', true);  // Highlight the bib number
        }
        noteInputs.forEach(input => {
            input.value = notesDictionary[bib]; // Set the value from the notesDictionary
        });
    }

}


function getCurrentDateTime() {
    const now = new Date();
    const year = String(now.getFullYear()).slice(-2); // Get last two digits of the year
    const month = String(now.getMonth() + 1).padStart(2, '0'); // Months are 0-based
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}


"""
