console.log("Hi there! Feel to explore the code!");
//let apiURL = 'http://127.0.0.1:80/api'
let apiURL = "/api";
let playersTableOriginal = $("#onlinePlayersTable").html();
let saveGamesTableOriginal = $("#saveGamesTable").html();

let oldMsg = "";
let oldSettings = {};
let oldPlayers = {};
let oldSaves = {};
let isAdmin = false;

const statusMsg = (msg) => {
    if (oldMsg != msg) {
        oldMsg = msg;
        $("#serverStatus").removeClass(
            "text-success text-warning text-danger text-info"
        );
        if (msg == "off") {
            $("#serverStatus").text("Offline");
            $("#serverStatus").addClass("text-danger");
            $("#msg h5").text("Server is offline");
            $("#msg").collapse("show");
        } else if (msg == "shutdown") {
            $("#serverStatus").text("Shutting Down");
            $("#serverStatus").addClass("text-danger");
            $("#msg h5").text("Server is shutting down");
            $("#msg").collapse("hide");
        } else if (msg == "starting") {
            $("#serverStatus").text("Starting");
            $("#serverStatus").addClass("text-warning");
            $("#msg h5").text("Server is getting ready");
            $("#msg").collapse("show");
        } else if (msg == "saving") {
            $("#serverStatus").text("Saving");
            $("#serverStatus").addClass("text-info");
            $("#msg h5").text("Server is saving");
            $("#msg").collapse("hide");
        } else if (msg == "reboot") {
            $("#serverStatus").text("Rebooting");
            $("#serverStatus").addClass("text-info");
            $("#msg h5").text("Server is rebooting");
            $("#msg").collapse("hide");
        } else if (msg == "ready") {
            $("#serverStatus").text("Ready");
            $("#serverStatus").addClass("text-success");
            $("#msg h5").text("Server is ready");
            $("#msg").collapse("hide");
        } else if (msg == "delsave") {
            $("#serverStatus").text("Deleting Save");
            $("#serverStatus").addClass("text-danger");
            $("#msg h5").text("Server is deleting a Save");
            $("#msg").collapse("hide");
        } else if (msg == "loadsave") {
            $("#serverStatus").text("Loading Save");
            $("#serverStatus").addClass("text-warning");
            $("#msg h5").text("Server is loading a Save");
            $("#msg").collapse("hide");
        } else if (msg == "newsave") {
            $("#serverStatus").text("Creating New Save");
            $("#serverStatus").addClass("text-success");
            $("#msg h5").text("Server is creating a new Save");
            $("#msg").collapse("hide");
        } else if (msg == "renamesave") {
            $("#serverStatus").text("Renaming Save");
            $("#serverStatus").addClass("text-warning");
            $("#msg h5").text("Server is renaming a Save");
            $("#msg").collapse("hide");
        }
    }
};
const compareObj = (obj1, obj2) => {
    return JSON.stringify(obj1) === JSON.stringify(obj2);
};

let logList = [];
let webSocket = null;
const createWebSocket = async () => {
    let WSprotocol = location.protocol == "https:" ? "wss" : "ws";
    webSocket = new WebSocket(WSprotocol + "://" + location.host + "/ws");
    webSocket.onmessage = function (evt) {
        tick(evt.data);
    };
    webSocket.onopen = function (evt) {
        console.log("Created Web Socket");
    };
};
const checkWebSocket = async () => {
    if (webSocket.readyState === WebSocket.CLOSED) {
        try {
            createWebSocket();
        } catch {}
    }
};
createWebSocket();

setInterval(checkWebSocket, 5000);

const tick = async (data) => {
    if (data == {}) {
        return;
    }
    data = JSON.parse(data);
    console.log(data);
    try {
        statusMsg(data.status);
        isAdmin = data.admin;
        if ($("#console").length && !isAdmin) {
            location.reload();
        }
        if (data.forceUpdate) {
            oldMsg = "";
            oldSettings = {};
            oldPlayers = {};
            oldSaves = {};
        }
        if (data.hasUpdate != false) {
            let ghLink = document.querySelector("#githubLink");
            let tipInstance = ghLink._tippy;
            tipInstance.setContent("Update Available: " + data.hasUpdate);
            tipInstance.show();
        }
        // smart scroll
        if (isAdmin) {
            let log = $("#consoleText")[0];
            let isBottom = log.scrollTop == log.scrollHeight - log.clientHeight;

            let sLogs = data.logs.split(/\r?\n/);
            let newLogs = sLogs.filter((i) => !logList.includes(i) && i != "");

            newLogs.forEach((entry) => {
                logList.push(entry);

                let content = "";
                let levelType = "";
                entry = entry.replace(/"|'/g, "");
                entry = linkify(entry);

                if (entry.includes("INFO")) {
                    levelType = "INFO";
                    let parts = entry.split("INFO");
                    content =
                        "<i class='fas fa-info-circle iconInfo'></i> " +
                        parts[0] +
                        //"<span style='color: green;'>INFO</span>" +
                        parts[1];
                } else if (entry.includes("WARNING")) {
                    let parts = entry.split("WARNING");
                    levelType = "WARNING";
                    content =
                        "<i class='fas fa-exclamation-triangle iconWarn'></i> " +
                        parts[0] +
                        //"<span style='color: red;'>WARNING</span>" +
                        parts[1];
                } else {
                    content = entry;
                }

                let row = document.createElement("div");
                row.innerHTML = content;
                if (levelType == "WARNING") {
                    $(row).addClass("warning");
                }

                $("#consoleText").append(row);
            });

            if (isBottom) log.scrollTop = log.scrollHeight - log.clientHeight;
        }

        s = data.settings;
        if (data.stats) {
            $("#hWL").text(
                DOMPurify.sanitize(data.stats.isEnforcingWhitelist.toString())
            );
            $("#hPW").text(
                DOMPurify.sanitize(data.stats.hasServerPassword.toString())
            );
            $("#hCM").text(
                DOMPurify.sanitize(data.stats.creativeMode.toString())
            );

            $("#serverVersion").text(DOMPurify.sanitize(data.stats.build));
            $("#framerateStats").text(
                DOMPurify.sanitize(
                    parseInt(data.stats.averageFPS) +
                        "/" +
                        parseInt(s.MaxServerFramerate) +
                        " FPS"
                )
            );
        }
        if (!compareObj(oldSettings, s)) {
            oldSettings = s;
            bannerServerName;
            $("#bannerServerName").text(DOMPurify.sanitize(`${s.ServerName}`));
            $("#serverName").text(DOMPurify.sanitize(`${s.ServerName}`));
            $("#serverPort").text(
                DOMPurify.sanitize(`${s.PublicIP}:${s.Port}`)
            );
            $("#owner").text(DOMPurify.sanitize(s.OwnerName));
        }
        if (
            data.status == "starting" ||
            data.status == "off" ||
            data.status == "shutdown"
        ) {
            $("#playersStats").text("");
            $("#serverVersion").text("");
            $("#framerateStats").text("");
        } else {
            if (data.hasOwnProperty("savegames")) {
                if (!compareObj(oldSaves, data.savegames)) {
                    $("#saveGamesTable").html(saveGamesTableOriginal);
                    if (data.savegames.hasOwnProperty("gameList")) {
                        let gameList = Object.create(data.savegames.gameList);
                        gameList.sort((a, b) =>
                            a.active < b.active
                                ? 1
                                : a.active === b.active
                                ? a.name > b.name
                                    ? 1
                                    : -1
                                : -1
                        );
                        gameList.forEach((sg) => {
                            let row = document.createElement("tr");
                            sg.active == "Active"
                                ? $(row).addClass("activeSave")
                                : null;
                            row.innerHTML = `
                            <td class="d-md-none p-0 ${
                                sg.active == "Active" ? "activeCell" : ""
                            }"></td>
                            <td class="d-none d-md-table-cell">${DOMPurify.sanitize(
                                sg.active
                            )}</td>
                                <td><span data-name="${sg.name}" class="${
                                sg.active ? "" : "saveName"
                            }">${DOMPurify.sanitize(sg.name)}</span></td>
                                <td>${DOMPurify.sanitize(sg.date)}</td>
                                <td>${sg.bHasBeenFlaggedAsCreativeModeSave}</td>
                                <td>${DOMPurify.sanitize(sg.size)}</td>
                                <td>${createSaveActionButtons(
                                    sg.active,
                                    sg
                                )}</td>`;

                            $("#saveGamesTable>tbody").append(row);
                        });
                        oldSaves = data.savegames;
                    }
                }
            }

            if (!compareObj(oldPlayers, data.players)) {
                oldPlayers = data.players;
                $("#onlinePlayersTable").html(playersTableOriginal);
                $("#offlinePlayersTable").html(playersTableOriginal);
                if (data.players.hasOwnProperty("playerInfo")) {
                    $("#playersStats").text(
                        DOMPurify.sanitize(
                            data.players.playerInfo.filter((p) => p.inGame)
                                .length +
                                "/" +
                                s.MaximumPlayerCount
                        )
                    );

                    if (data.players) {
                        data.players.playerInfo.forEach((p) => {
                            let row = document.createElement("tr");
                            row.innerHTML = `<td class="p-2 d-md-none" >
                            ${DOMPurify.sanitize(
                                p.playerName == "" ? " " : p.playerName
                            )}
                            <hr class="m-1">
                            ${DOMPurify.sanitize(p.playerGuid)}</td>

                            <td class="p-2 d-none d-md-table-cell" >
                                ${DOMPurify.sanitize(p.playerName)}
                            </td>
                            <td class="p-2 d-none d-md-table-cell">
                                ${DOMPurify.sanitize(p.playerGuid)}
                            </td>

                            <td class="text-left">${DOMPurify.sanitize(
                                p.playerCategory
                            )}</td>`;

                            if (p.inGame == true) {
                                if (isAdmin) {
                                    row.innerHTML +=
                                        '<td class="text-left">' +
                                        createPlayerActionButtons("online", p) +
                                        "</td>";
                                }
                                $("#onlinePlayersTable>tbody").append(row);
                            } else {
                                $("#offlinePlayersTable>tbody").append(row);
                                if (isAdmin) {
                                    row.innerHTML +=
                                        '<td class="text-left">' +
                                        createPlayerActionButtons(
                                            "offline",
                                            p
                                        ) +
                                        "</td>";
                                }
                            }
                        });
                    }
                }
            }
        }
    } catch (e) {
        console.log(e);
        $("#msg h5").text("ERROR! Try again in 10s");
        $("#msg").collapse("show");
        statusMsg("off");
    }
};

const createSaveActionButtons = function (status, save) {
    dropDownDiv = $("<div/>").attr({ class: "btn-group dropup" });
    DDButton = $("<button/>")
        .attr({
            type: "button",
            class: "btn btn-secondary dropdown-toggle",
            "data-toggle": "dropdown",
            "aria-haspopup": "true",
            "aria-expanded": "false",
            id: "dropdownMenu2",
        })
        .text("Actions");
    DDMenu = $("<div/>").attr({
        class: "dropdown-menu",
        "aria-labelledby": "dropdownMenu2",
    });
    dropDownDiv.append(DDButton);
    dropDownDiv.append(DDMenu);
    sButton = $("<button/>").attr({
        type: "button",
        class: "dropdown-item p-1",
        "data-name": save.name,
    });

    actionButtonBufferList = [];

    loadButton = sButton
        .clone()
        .attr("data-action", "load")
        .addClass("sBtn")
        .text("Load");
    actionButtonBufferList.push(loadButton);

    deleteButton = sButton
        .clone()
        .addClass("sdBtn")
        .attr("data-action", "delete")
        .attr("data-toggle", "modal")
        .attr("data-target", "#deleteSaveModal")
        .text("Delete");
    actionButtonBufferList.push(deleteButton);

    renameButton = sButton
        .clone()
        .addClass("sdBtn")
        .attr("data-action", "rename")
        .text("Rename");
    actionButtonBufferList.push(renameButton);

    if (status == "Active") {
        loadButton.addClass("disabled");
        deleteButton.addClass("disabled");
    }

    actionButtonBufferList.forEach((element) => {
        DDMenu.append(element);
    });
    return dropDownDiv.prop("outerHTML");
};

const createPlayerActionButtons = function (status, player) {
    dropDownDiv = $("<div/>").attr({ class: "btn-group dropup" });
    DDButton = $("<button/>")
        .attr({
            type: "button",
            class: "btn btn-secondary dropdown-toggle",
            "data-toggle": "dropdown",
            "aria-haspopup": "true",
            "aria-expanded": "false",
            id: "dropdownMenu2",
        })
        .text("Actions");
    DDMenu = $("<div/>").attr({
        class: "dropdown-menu",
        "aria-labelledby": "dropdownMenu2",
    });
    dropDownDiv.append(DDButton);
    dropDownDiv.append(DDMenu);
    sButton = $("<button/>").attr({
        type: "button",
        class: "dropdown-item pBtn p-1",
        "data-guid": player.playerGuid,
        "data-name": player.playerName,
    });

    actionButtonBufferList = [];
    if (player.playerCategory != "Owner") {
        kickButton = sButton.clone().attr("data-action", "kick").text("Kick");
        actionButtonBufferList.push(kickButton);

        banButton = sButton.clone().attr("data-action", "ban").text("Ban");
        actionButtonBufferList.push(banButton);

        WLButton = sButton.clone().attr("data-action", "WL").text("Whitelist");
        actionButtonBufferList.push(WLButton);

        AdminButton = sButton
            .clone()
            .attr("data-action", "admin")
            .text("Give Admin");
        actionButtonBufferList.push(AdminButton);

        ResetButton = sButton
            .clone()
            .attr("data-action", "reset")
            .text("Reset Perms");
        actionButtonBufferList.push(ResetButton);

        /*
        RemoveButton = sButton
            .clone()
            .attr("data-action", "remove")
            .text("Remove");
        actionButtonBufferList.push(RemoveButton);
        */
        if (status != "online") {
            kickButton.addClass("disabled");
        }
        if (player.playerCategory == "Blacklisted") {
            banButton.addClass("disabled");
        }
        if (player.playerCategory == "Whitelisted") {
            WLButton.addClass("disabled");
        }
        if (player.playerCategory == "Admin") {
            AdminButton.addClass("disabled");
        }
        if (player.playerName == "") {
            kickButton.addClass("disabled");
            banButton.addClass("disabled");
            WLButton.addClass("disabled");
            AdminButton.addClass("disabled");
            ResetButton.addClass("disabled");
        }
    }
    actionButtonBufferList.forEach((element) => {
        DDMenu.append(element);
    });
    return dropDownDiv.prop("outerHTML");
};
$(document).on("input", "#WLPlayerInp", function (e) {
    console.log($(e.target).val());
    $("#WLPlayerBtn").attr({ "data-name": $(e.target).val() });
});

$(document).on("click", "button[data-action='rename']", function (e) {
    oName = $(e.target).attr("data-name");
    nameSpan = $(`span[data-name='${oName}']`);
    sName = nameSpan.text();
    swidth = nameSpan.width();
    parent = nameSpan.parent();
    parent.addClass("inputBox");
    a = $("<div/>").attr({
        class: "input-group mb-3",
    });
    b = $("<div/>").attr({
        class: "input-group-append",
    });

    sInput = $("<input/>").attr({
        type: "text",
        class: "saveNameInput form-control",
        "data-saveOName": sName,
    });
    sInput.val(sName);
    sButton = $("<button/>")
        .attr({
            type: "button",
            class: "saveNameSubmit btn btn-outline-secondary text-white",
            "data-saveOName": sName,
        })
        .text("✓");
    parent.html("");
    a.append(sInput);
    b.append(sButton);
    a.append(b);
    parent.append(a);
});

$(document).on("click", ".saveNameSubmit", function (e) {
    e.preventDefault();
    parent = $(e.target).closest(".inputBox");
    parent.removeClass("inputBox");
    sInput = parent.find(".saveNameInput");
    sName = sInput.val();
    oName = $(e.target).attr("data-saveOName");
    if (sName.length < 3) {
        sName = oName;
    }
    if (
        !oldSaves.gameList.map((x) => x.name).includes(sName) &&
        oName != sName
    ) {
        $.ajax({
            type: "POST",
            url: apiURL + "/savegame/rename",
            dataType: "json",
            data: JSON.stringify({ oName: oName, nName: sName }),
            success: function (result) {},
            error: function (result) {
                console.log(result);
                alert("Error");
            },
        });
    } else {
        sName = oName;
    }
    nameSpan = $("<span/>").addClass("saveName").attr("data-name", sName);
    nameSpan.text(sName);
    parent.html(nameSpan);
});

$(document).on("click", ".pBtn", function (e) {
    e.preventDefault();
    pGuid = $(e.target).attr("data-guid");
    pName = $(e.target).attr("data-name");
    pAction = $(e.target).attr("data-action");

    $.ajax({
        type: "POST",
        url: apiURL + "/player",
        dataType: "json",
        data: JSON.stringify({ guid: pGuid, action: pAction, name: pName }),
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$(document).on("click", ".sBtn", function (e) {
    e.preventDefault();
    sName = $(e.target).attr("data-name");
    sAction = $(e.target).attr("data-action");
    $.ajax({
        type: "POST",
        url: apiURL + "/savegame/" + sAction,
        dataType: "json",
        data: JSON.stringify({ name: sName }),
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$("#deleteSaveModal").on("show.bs.modal", function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    var saveName = button.data("name"); // Extract info from data-* attributes
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    var save = oldSaves["gameList"].find((obj) => {
        return obj.name === saveName;
    });
    var fullSaveName = DOMPurify.sanitize(
        save["name"] + "$" + save["date"] + ".savegame"
    );
    var modal = $(this);
    modal
        .find(".modal-title")
        .text("Are you sure you wish to delete this save? ");
    modal
        .find(".modal-body")
        .text(DOMPurify.sanitize(fullSaveName + " -- " + save["size"]));
    modal
        .find(".modal-footer .btn-danger")
        .attr("data-action", "delete")
        .attr("data-name", saveName);
});

const saveLog = function (filename, data) {
    var blob = new Blob([data], { type: "text/csv" });
    if (window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveBlob(blob, filename);
    } else {
        var elem = window.document.createElement("a");
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;
        document.body.appendChild(elem);
        elem.click();
        document.body.removeChild(elem);
    }
};

$(".fa-download").click(function (e) {
    e.stopPropagation();

    fileBuffer = "";
    logList.forEach((entry) => {
        fileBuffer += entry;
        fileBuffer += "\n";
    });

    saveLog("server.log", fileBuffer);
});

$("#saveGameBtn").click(function (e) {
    e.preventDefault();
    statusMsg("saving");
    $.ajax({
        type: "POST",
        url: apiURL + "/savegame",
        dataType: "json",
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$("#rebootServerBtn").click(function (e) {
    e.preventDefault();
    statusMsg("reboot");
    $.ajax({
        type: "POST",
        url: apiURL + "/reboot",
        dataType: "json",
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

$("#stopLauncherBtn").click(function (e) {
    e.preventDefault();
    statusMsg("shutdown");
    let reallyShutdown = confirm(
        "Are you sure you want to shut down the launcher? It will have to be manually restarted."
    );
    if (reallyShutdown == true) {
        setTimeout(() => {
            statusMsg("off");
        }, 2000);
        $.ajax({
            type: "POST",
            url: apiURL + "/shutdown",
            dataType: "json",
            success: function (result) {},
            error: function (result) {
                console.log(result);
            },
        });
    }
});

$("#newSaveBtn").click(function (e) {
    e.preventDefault();
    e.stopPropagation();
    statusMsg("saving");
    $.ajax({
        type: "POST",
        url: apiURL + "/newsave",
        dataType: "json",
        success: function (result) {},
        error: function (result) {
            console.log(result);
            alert("Error");
        },
    });
});

const linkify = (text) => {
    //const exp = /(\b(((https?|ftp|file):\/\/)|[-A-Z0-9+&@#\/%=~_|]*\.)[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi;
    const exp = /(\b(((https?|ftp|file):\/\/)|[-A-Z+&@#\/%=~_|]+\.)[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gi;
    text = DOMPurify.sanitize(text);
    return text.replace(
        exp,
        `<a href="$1" target="_blank" style="color: #baf;">$1</a>`
    );
};

var clipboard = new ClipboardJS(".ctc");

clipboard.on("success", function (e) {
    e.clearSelection();
});

tippy(".ctc", {
    content: "Copied!",
    trigger: "click",
    onShow(instance) {
        setTimeout(() => {
            instance.hide();
        }, 1500);
    },
    placement: "right",
});

tippy(".ctc", {
    content: "Click to Copy",
    trigger: "mouseenter focus",
    placement: "right",
    onTrigger(instance, event) {
        if (tippy.currentInput.isTouch) {
            instance.disable();
        } else {
            instance.enable();
        }
    },
});

tippy("#githubLink", {
    content: "Update Available",
    placement: "right-end",
    trigger: "manual",
    hideOnClick: false,
    theme: "update",
    interactive: true,
});
