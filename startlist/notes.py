notes = """
var notesDictionary = {};  // Dictionary to store notes keyed by bib number

//var lastBibNumber = null;
function openNoteBib(bibNumber, setFlag, debug = false) {
    console.log('---------------------------------------------');
    console.log('---------------------------------------------');
    //console.log('highlightBibNumber:', bibNumber, highlightColor, setFlag);
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
            /*
            if (bibCell.innerText === bibNumber) {
                //console.log('searchBibNumber: %s found table: %s row: %d id: %s XXX', bibNumber, table.id, i, rows[i].id);
                foundFlag = true;
                rows[i].querySelectorAll('td').forEach(function(td) {
                    if (!setFlag) { setFlag = td.style.backgroundColor === 'white'; }
                    td.style.backgroundColor = setFlag ? highlightColor : 'white';
                });
            }
            */
        }
    });
    console.log('searchBibNumber: foundFlag:', foundFlag);
    return foundFlag;
}

// Toggle visibility of the note row
function toggleNoteRow(bib, noteId) {
    console.log('toggleNoteRow: bib: %s noteId: %s', bib, noteId);
    var noteRow = document.getElementById(noteId);
    console.log('toggleNoteRow: noteRow.placeholder: %s', noteRow.placeholder);
    //console.log('toggleNoteRow: noteRow.style: %s', noteRow.style);
    //console.log('toggleNoteRow: noteRow.style.display: %s', noteRow.style.display);

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

    console.log('note for bib: %s: event value: %s', bib, event.target.value.trim()); 

    // Update notesDictionary with the new note value
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
    notesData = "Competition Notes: " + event + "\\n";
    notesData += "Date: " + date + "\\n\\n";
    notesData += "Generated: " + getCurrentDateTime() + "\\n";
    notesData += "----------------------------------\\n\\n";

    Object.keys(notesDictionary).forEach(function(bib) {
        notesData += "Bib: " + bib + "\\n";
        notesData += notesDictionary[bib] + "\\n";
        notesData += "----------------------------------\\n";
    });

    let filename = date + '_' + event + '_notes';
    const blob = new Blob([notesData], { type: 'text/plain' });
    const file = new File([blob], filename+'.txt', { type: 'text/plain' });

    if (navigator.canShare && navigator.canShare({ files: [file] })) {
        alert("Sharing supported.");
        //alert("Shared file created.");
        navigator.share({
            title: filename,
            files: [file]
        }).then(() => {
            alert("Shared success.");
            console.log('Shared successfully');
        }).catch((error) => {
            alert("Shared error.");
            console.error('Error sharing:', error);
        });
        alert("Shared. finished");
    } else {
        customAlert("Sharing not supported, download.", 5000);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename+'.txt';  // Set file name
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
        console.log('restoreNotes: selectors:', selectors);
        console.dir(selectors);
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
