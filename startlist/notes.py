notes = """
var notesDictionary = {};  // Dictionary to store notes keyed by bib number

//var lastBibNumber = null;
function openNoteBib(bibNumber, setFlag, debug = false) {
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
                //console.log('searchBibNumber: %s found table: %s row: %d id: %s XXX', bibNumber, table.id, i, rows[i].id);
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

let xbigHighlighted = [];
function xtoggleBib(bibId) {
    console.log('toggleBib:', bib);

    var allTables = document.querySelectorAll('table[id*="_wave_"]');
    foundFlag = false;
    allTables.forEach(function(table) {
        console.log('searchNoteNumber: table:', table.id);

    })

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


// Toggle visibility of the note row
function toggleNoteRow(bib, noteId) {
    console.log('toggleNoteRow: bib: %s noteId: %s', bib, noteId);
    var noteRow = document.getElementById(noteId);
    if (noteRow.style.display === 'none') {
        noteRow.style.display = 'table-row';
    } else {
        noteRow.style.display = 'none';
    }
}

// Handle keypress event
function handleNoteKeyPress(event, bib, inputId) {
    console.log('handleNoteKeyPress: bib: %s %s', inputId, event.key);
    if (event.key === 'Enter') {
        console.log('handleNoteKeyPress: call saveNoteData');
        saveNoteData(bib, inputId);  // Save the note when Enter is pressed
    }
}

// Handle keydown event (you can extend this if needed)
function handleNoteKeyDown(event, bib, inputId) {
    // Optional: Additional handling on key down
    //var noteInput = document.querySelector(inputId);
    var noteInput = document.getElementById(inputId);
    console.log('handleNoteKeyDown: bib: %s inputId: %s: noteInput: %s', bib, inputId, noteInput);
    if (noteInput) {
        console.log('note for bib: %s: value: %s', bib, noteInput.value); 
    }
}

// Save the note data when the input field loses focus or Enter is pressed
function saveNoteData(bib, inputId) {
    //var noteInput = document.querySelector(inputId);
    var noteInput = document.getElementById(inputId);
    console.log('saveNoteData: bib: %s inputId: %s: noteInput: %s', bib, inputId, noteInput);
    if (noteInput) {
        notesDictionary[bib] = noteInput.value;
        console.log('Saved note for bib: %s: value: %s', bib, noteInput.value); 
    }
}

function XXXdownloadNotes_file() {
    console.log('downloadNotes: notesDictionary:', notesDictionary);
    const notesData = JSON.stringify(notesDictionary, null, 2);  // Save as JSON or format as text
    const blob = new Blob([notesData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'notes.txt';  // Set file name
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
    //const file = new File([blob], 'race_notes.txt', { type: 'text/plain' });
    //const file = new File([blob], date + '_' + event + '_notes.txt', { type: 'text/plain' });
    const file = new File([blob], filename+'.txt', { type: 'text/plain' });

    //alert("Checking for sharing support.");
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
