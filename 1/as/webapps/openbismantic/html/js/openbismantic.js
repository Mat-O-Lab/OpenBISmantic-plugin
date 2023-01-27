let v3;

function switchView(...viewNames) {
    const viewIds = viewNames.map(viewName => `${viewName}-view`);
    for (let viewElement of document.getElementsByClassName('view'))
        viewElement.style.display = viewIds.includes(viewElement.id) ? 'block' : '';
    window.scrollTo(0, 0);
}

/*
    Allowed levels: primary, success, warning, danger, info, light, dark
*/
function showAlert(message, level, timeout) {
    const alertElem = document.createElement('div');
    alertElem.className = 'alert alert-dismissible fade show alert-' + (level || 'info');
    alertElem.setAttribute('role', 'alert');
    const alertMessage = document.createElement('span');
    alertMessage.textContent = message;
    alertElem.appendChild(alertMessage);
    const alertCloseButton = document.createElement('button');
    alertCloseButton.type = 'button';
    alertCloseButton.className = 'btn-close';
    alertCloseButton.setAttribute('data-bs-dismiss', 'alert');
    alertCloseButton.setAttribute('aria-label', 'Close');
    alertElem.appendChild(alertCloseButton);
    if (timeout) {
        setTimeout(() => alertCloseButton.click(), timeout);
    }
    document.getElementById('messages').appendChild(alertElem);
}

function initUi() {
    document.getElementById('login-form').addEventListener('submit', e => {
        console.log(e.target);
        const user = e.target.querySelector('#user-input').value;
        const password = e.target.querySelector('#password-input').value;
        v3.login(user, password).done(token => {
            localStorage.setItem('openbis-token', token);
            switchView('export');
        }).fail(() => {
            showAlert('login failed', 'warning', 2500);
        });
        e.preventDefault();
    });
    document.getElementById('logout-button').addEventListener('click', () => {
        localStorage.removeItem('openbis-token');
        v3.logout().then(() => {
            switchView('login');
        });
    });
    for (let viewNav of ['export']) {
        document.getElementById(`nav-${viewNav}`).addEventListener('click', () => {
            if (v3._private.sessionToken)
                switchView(viewNav);
        });
    }
    document.getElementById('export-button').addEventListener('click', () => recursiveExport());
    document.getElementById('query-input').addEventListener('keypress', ev => {
        if (ev.key === 'Enter')
            recursiveExport();
    });
    switchView('login');
}

function saveFile(result, fileName) {
    console.log('saving file', fileName);
    const data = JSON.stringify(stjsUtil.decycle(result), null, 2);
    const blob = new Blob([data], {type: 'application/json;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileName}.json`;
    link.click();
    URL.revokeObjectURL(url);
}

function recursiveExport(permID) {
    if (permID === undefined)
        permID = document.getElementById('query-input').value;
    const options = new CustomASServiceExecutionOptions();
    options.withParameter('method', 'recursiveExport');
    options.withParameter('permID', permID);
    v3.executeCustomASService(new CustomASServiceCode("openbismantic-api"), options).then(res => {
        document.getElementById('export-log').innerText = '';
        saveFile(res, res[permID].code.toLowerCase());
    }).fail(e => {
        document.getElementById('export-log').innerText = e.data.message + '\n\n' + e.data.stackTrace;
    });
}


document.addEventListener('DOMContentLoaded', () => {
    require(["openbis",
        "util/Json",
        "as/dto/sample/fetchoptions/SampleFetchOptions",
        "as/dto/service/id/CustomASServiceCode",
        "as/dto/service/CustomASServiceExecutionOptions"
    ], function (openbis,
                 stjsUtil,
                 SampleFetchOptions,
                 CustomASServiceCode,
                 CustomASServiceExecutionOptions) {
        window.stjsUtil = stjsUtil;
        window.SampleFetchOptions = SampleFetchOptions;
        window.CustomASServiceCode = CustomASServiceCode;
        window.CustomASServiceExecutionOptions = CustomASServiceExecutionOptions;
        v3 = new openbis();
        const restoredToken = localStorage.getItem('openbis-token');
        if (restoredToken) {
            v3._private.sessionToken = restoredToken;
            v3.isSessionActive().done(success => {
                if (success) {
                    switchView('export');
                } else {
                    showAlert('session expired', 'warning');
                    localStorage.removeItem('openbis-token');
                }
            });
        }
        document.getElementById('loading-overlay').style.display = 'none';
    });
    initUi();
});

