
css = """
html, body {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    overflow-x: hidden; /* Prevent any hidden overflow */
}

.container {
    display: flex;
    flex-direction: column;
    width: 100vw;
    height: 100vh; /* Ensure the container fills the entire viewport */
    padding: 0;
    margin: 0;
    max-width: none;
    max-height: none;
}

.left, {
    padding: 0;
    margin: 0;
}

.right {
    flex-grow: 1;
    padding: 0;
    margin: 0;
    overflow-y: auto;  /* Enable vertical scrolling */
}


thead {
  display: table-header-group;
}
/*
.fs-s { font-size: .7em; }
.fs-m { font-size: .9em; }
.fs-l { font-size: 1.3em; }
.fs-xl { font-size: 1.4em; }
.fs-20px { font-size: 20px; 
*/

.select-tr { padding: 1px !important; text-align: center; width: 100%; }
.select-thtd { padding: 1px !important; text-align: center; }

.part-table {
    border-collapse: collapse;
    border: none !important;
    margin: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    width: 100% !important;
    box-sizing: border-box;

}
.part-thead {
    align-items: start;
    position: sticky;  /* Make the header sticky */
    background-color: white;
    top: 0;
    border-spacing: 0;
    width: 100% !important;
}
.part-tbody {
    align-items: start;
    /*position: sticky;*/  /* Make the header sticky */
    background-color: white;
    top: 0;
    border-spacing: 0;
    width: 100% !;
}
.part-tr-s { 
    align-items: end;
    margin: 0;
    padding: 0 !important; 
    text-align: center; 
    width: 100% !important; 
    border-spacing: 0;
    border: none !important;
    line-height: 1.5;   
    font-size: .7em;
}
.part-tr-15 { 
    align-items: end;
    margin: 0;
    padding: 0 !important; 
    text-align: center; 
    width: 100% !important; 
    border-spacing: 0;
    border: none !important;
    line-height: 1.5;   
}
.part-tr { 
    align-items: end;
    margin: 0;
    padding: 0 !important; 
    text-align: center; 
    width: 100% !important; 
    border-spacing: 0;
    border: none !important;
}
/* participant */
.thtd { 
    padding: 1px !important; 
    text-align: center; 
    border-spacing: 0;
    vertical-align: middle !important; 
    box-sizing: border-box;
}
.thtd-xl { 
    padding: 1px !important; 
    text-align: center; 
    border-spacing: 0;
    vertical-align: middle !important; 
    box-sizing: border-box;
    font-size: 1.4em;
}
.thtd-left { 
    padding: 1px !important; 
    text-align: left; 
    border-spacing: 0;
    vertical-align: middle !important; 
    box-sizing: border-box;
}
.thtd-28 { 
    padding: 1px !important; 
    text-align: center; 
    border-spacing: 0;
    vertical-align: middle !important; 
    box-sizing: border-box;
    width: 28px;
    margin-right: 10px;
    font-size: 1.4em;
}
/* notes */
//.participant-note:nth-child(4n+1) { background-color: red; }
//.participant-note:nth-child(even) { background-color: lightgreen; }


.part-note { 
    display: none;
    align-items: end;
    margin: 0;
    padding: 0 !important; 
    text-align: center; 
    width: 100% !important; 
    border-spacing: 0;
    border: none !important;
    background-color: white;
    font-size: .7em;
}

.note-input {
    width: 98%; 
    height: 100%; 
    padding: 1px; 
    border: 1px solid #ccc; 
    border-radius: 4px;
}
.div-note {
    position: relative;
    width: 100%;
}
.note-tr {
    background-color: white;
}

@media screen and (orientation: landscape) {
    .container {
        flex-direction: row;
        width: 100vw;
        justify-content: stretch; /* Stretch the columns to fill the available space */
        gap: 20px
    }
    .left, .right {
        width: 50vw;
        height: 100vh; /* Ensure columns span the entire viewport height */
    }
}

input[type="text"] {
  position: relative;
}

.clearable {
  background: white;
}

.clear-button {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
}



@media screen and (min-width: 768px) and (max-width: 1024px) {
    /* Styles for tablets */
}
@media screen and (min-width: 1024px) {
    /* Styles for desktop browsers */
}



"""

