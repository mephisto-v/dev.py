#include <QApplication>
#include <QMainWindow>
#include <QTreeWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QTextEdit>
#include <QFileDialog>
#include <QMessageBox>
#include <QInputDialog>
#include <QThread>
#include <libsmbclient.h>
#include <fstream>
#include <vector>
#include <string>
#include <iostream>

// Structure to hold file information
struct SMBEntry {
    std::string name;
    size_t size;
    std::string type; // "File" or "Directory"
};

// SMB Client Backend
class SMBClient {
public:
    SMBClient() : smbContext(nullptr) {
        smbc_init([](const char *srv, const char *sharename, char *workgroup, int wglen, char *username, int unlen, char *password, int pwlen) {}, 0);
    }

    ~SMBClient() {
        if (smbContext) smbc_free_context((smbc_context *)smbContext, 1);
    }

    bool connect(const std::string &server, const std::string &username, const std::string &password) {
        smbContext = smbc_new_context();
        if (!smbContext) return false;

        smbc_setOptionUserData((smbc_context *)smbContext, nullptr);
        smbc_setOptionUser((smbc_context *)smbContext, username.c_str());
        smbc_setOptionPassword((smbc_context *)smbContext, password.c_str());

        return smbc_init_context((smbc_context *)smbContext) == 0;
    }

    std::vector<SMBEntry> listDirectory(const std::string &path) {
        std::vector<SMBEntry> entries;
        SMBCFILE *dir = smbc_opendir(path.c_str());
        if (!dir) return entries;

        struct smbc_dirent *entry;
        while ((entry = smbc_readdir(dir)) != nullptr) {
            SMBEntry smbEntry;
            smbEntry.name = entry->name;
            smbEntry.type = (entry->smbc_type == SMBC_DIR) ? "Directory" : "File";
            entries.push_back(smbEntry);
        }
        smbc_closedir(dir);
        return entries;
    }

    bool uploadFile(const std::string &localPath, const std::string &remotePath) {
        std::ifstream file(localPath, std::ios::binary);
        if (!file.is_open()) return false;

        SMBCFILE *remoteFile = smbc_creat(remotePath.c_str(), 0666);
        if (!remoteFile) return false;

        char buffer[4096];
        while (file.read(buffer, sizeof(buffer))) {
            smbc_write(remoteFile, buffer, file.gcount());
        }
        smbc_close(remoteFile);
        file.close();
        return true;
    }

    bool downloadFile(const std::string &remotePath, const std::string &localPath) {
        SMBCFILE *remoteFile = smbc_open(remotePath.c_str(), O_RDONLY, 0);
        if (!remoteFile) return false;

        std::ofstream file(localPath, std::ios::binary);
        if (!file.is_open()) {
            smbc_close(remoteFile);
            return false;
        }

        char buffer[4096];
        ssize_t bytesRead;
        while ((bytesRead = smbc_read(remoteFile, buffer, sizeof(buffer))) > 0) {
            file.write(buffer, bytesRead);
        }

        smbc_close(remoteFile);
        file.close();
        return bytesRead == 0;
    }

    bool deleteFile(const std::string &remotePath) {
        return smbc_unlink(remotePath.c_str()) == 0;
    }

private:
    void *smbContext; // Pointer to libsmbclient context
};

// Main Window
class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr) : QMainWindow(parent), currentPath("/") {
        setWindowTitle("Sophisticated SMB Client 🌐");

        QWidget *centralWidget = new QWidget(this);
        QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

        // Tree widget to display files
        treeWidget = new QTreeWidget(this);
        treeWidget->setColumnCount(2);
        treeWidget->setHeaderLabels({"File Name", "Type"});
        connect(treeWidget, &QTreeWidget::itemDoubleClicked, this, &MainWindow::onFileSelected);
        mainLayout->addWidget(treeWidget);

        // Buttons with emojis
        QHBoxLayout *buttonLayout = new QHBoxLayout();
        QPushButton *connectButton = new QPushButton("🔌 Connect", this);
        connect(connectButton, &QPushButton::clicked, this, &MainWindow::connectToServer);
        buttonLayout->addWidget(connectButton);

        QPushButton *uploadButton = new QPushButton("⬆️ Upload", this);
        connect(uploadButton, &QPushButton::clicked, this, &MainWindow::uploadFile);
        buttonLayout->addWidget(uploadButton);

        QPushButton *downloadButton = new QPushButton("⬇️ Download", this);
        connect(downloadButton, &QPushButton::clicked, this, &MainWindow::downloadFile);
        buttonLayout->addWidget(downloadButton);

        QPushButton *deleteButton = new QPushButton("❌ Delete", this);
        connect(deleteButton, &QPushButton::clicked, this, &MainWindow::deleteFile);
        buttonLayout->addWidget(deleteButton);

        QPushButton *refreshButton = new QPushButton("🔄 Refresh", this);
        connect(refreshButton, &QPushButton::clicked, this, &MainWindow::refreshDirectory);
        buttonLayout->addWidget(refreshButton);

        mainLayout->addLayout(buttonLayout);

        // Log area
        logArea = new QTextEdit(this);
        logArea->setReadOnly(true);
        mainLayout->addWidget(logArea);

        setCentralWidget(centralWidget);
    }

private slots:
    void connectToServer() {
        bool ok;
        QString server = QInputDialog::getText(this, "Connect to SMB Server", "Enter Server Address:", QLineEdit::Normal, "", &ok);
        if (!ok || server.isEmpty()) return;

        QString username = QInputDialog::getText(this, "Username", "Enter Username:", QLineEdit::Normal, "", &ok);
        if (!ok) return;

        QString password = QInputDialog::getText(this, "Password", "Enter Password:", QLineEdit::Password, "", &ok);
        if (!ok) return;

        if (!smbClient.connect(server.toStdString(), username.toStdString(), password.toStdString())) {
            log("❌ Connection failed!");
            QMessageBox::critical(this, "Connection Failed", "Unable to connect to the server.");
            return;
        }

        log("✅ Connected to server: " + server);
        browseDirectory("/");
    }

    void browseDirectory(const QString &path) {
        currentPath = path;
        auto entries = smbClient.listDirectory(path.toStdString());
        if (entries.empty()) {
            log("⚠️ Unable to browse directory: " + path);
            QMessageBox::warning(this, "Error", "Unable to browse directory.");
            return;
        }

        treeWidget->clear();
        for (const auto &entry : entries) {
            QTreeWidgetItem *item = new QTreeWidgetItem(treeWidget);
            item->setText(0, QString::fromStdString(entry.name));
            item->setText(1, QString::fromStdString(entry.type));
        }
        log("📂 Browsed directory: " + path);
    }

    void uploadFile() {
        QString filePath = QFileDialog::getOpenFileName(this, "Select File to Upload");
        if (filePath.isEmpty()) return;

        QString remotePath = currentPath + "/" + QFileInfo(filePath).fileName();
        if (smbClient.uploadFile(filePath.toStdString(), remotePath.toStdString())) {
            log("⬆️ Uploaded file: " + filePath);
            refreshDirectory();
        } else {
            log("❌ Failed to upload file: " + filePath);
            QMessageBox::warning(this, "Upload Failed", "Failed to upload file.");
        }
    }

    void downloadFile() {
        QTreeWidgetItem *selectedItem = treeWidget->currentItem();
        if (!selectedItem || selectedItem->text(1) != "File") {
            QMessageBox::warning(this, "No File Selected", "Please select a file to download.");
            return;
        }

        QString fileName = selectedItem->text(0);
        QString savePath = QFileDialog::getSaveFileName(this, "Save File As", fileName);
        if (savePath.isEmpty()) return;

        QString remotePath = currentPath + "/" + fileName;
        if (smbClient.downloadFile(remotePath.toStdString(), savePath.toStdString())) {
            log("⬇️ Downloaded file: " + fileName);
        } else {
            log("❌ Failed to download file: " + fileName);
            QMessageBox::warning(this, "Download Failed", "Failed to download file.");
        }
    }

    void deleteFile() {
        QTreeWidgetItem *selectedItem = treeWidget->currentItem();
        if (!selectedItem || selectedItem->text(1) != "File") {
            QMessageBox::warning(this, "No File Selected", "Please select a file to delete.");
            return;
        }

        QString fileName = selectedItem->text(0);
        QString remotePath = currentPath + "/" + fileName;
        if (smbClient.deleteFile(remotePath.toStdString())) {
            log("❌ Deleted file: " + fileName);
            refreshDirectory();
        } else {
            log("❌ Failed to delete file: " + fileName);
            QMessageBox::warning(this, "Delete Failed", "Failed to delete file.");
        }
    }

    void refreshDirectory() {
        browseDirectory(currentPath);
    }

    void onFileSelected(QTreeWidgetItem *item, int column) {
        if (item->text(1) == "Directory") {
            browseDirectory(currentPath + "/" + item->text(0));
        }
    }

private:
    void log(const QString &message) {
        logArea->append(message);
    }

    SMBClient smbClient;
    QTreeWidget *treeWidget;
    QTextEdit *logArea;
    QString currentPath;
};

// Main Function
int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    MainWindow mainWindow;
    mainWindow.show();
    return app.exec();
}
