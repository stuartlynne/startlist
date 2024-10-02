
js = """
    
$(document).ready(function () {
    $("table").tablesorter({
        theme: 'default',   // Default theme with sorting arrows
        widgets: ['zebra'], // Zebra striping effect for the rows
    });
});



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

"""
