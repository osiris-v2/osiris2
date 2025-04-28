#include <QApplication>
#include <QWidget>
#include <QVBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QMessageBox>
#include <cstdio> // For fprintf

// Define a struct to hold the widgets and their states
typedef struct {
    QWidget *window;
    QVBoxLayout *layout;
    QLabel *label;
    QPushButton *button;
    int clickCount;
} MainWindow;

// Function to handle button clicks
void buttonClicked(MainWindow *mainWindow) {
    mainWindow->clickCount++;
    QString message = QString("Button clicked %1 times").arg(mainWindow->clickCount);
    mainWindow->label->setText(message);

    // Show a message box after 5 clicks
    if (mainWindow->clickCount >= 5) {
        QMessageBox::information(mainWindow->window, "Information", "You've clicked the button 5 times!");
        mainWindow->clickCount = 0; // Reset the click count
        mainWindow->label->setText("Button clicked 0 times");
    }
}

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    // Allocate memory for the main window data
    MainWindow *mainWindow = (MainWindow *)malloc(sizeof(MainWindow));
    if (mainWindow == NULL) {
        fprintf(stderr, "Failed to allocate memory for MainWindow\n");
        return 1;
    }

    // Initialize MainWindow structure members
    mainWindow->clickCount = 0;

    // Create the main window
    mainWindow->window = new QWidget();
    mainWindow->window->setWindowTitle("Qt C Window Example");

    // Create a vertical layout
    mainWindow->layout = new QVBoxLayout();

    // Create a label
    mainWindow->label = new QLabel("Button clicked 0 times");
    mainWindow->layout->addWidget(mainWindow->label);

    // Create a button
    mainWindow->button = new QPushButton("Click Me");
    mainWindow->layout->addWidget(mainWindow->button);

    // Set the layout for the main window
    mainWindow->window->setLayout(mainWindow->layout);

    // Connect the button's clicked signal to the buttonClicked function
    QObject::connect(mainWindow->button, &QPushButton::clicked, [mainWindow]() {
        buttonClicked(mainWindow);
    });

    // Show the main window
    mainWindow->window->show();

    // Run the application event loop
    int result = app.exec();

    // Clean up resources
    delete mainWindow->button;
    delete mainWindow->label;
    delete mainWindow->layout;
    delete mainWindow->window;
    free(mainWindow);

    return result;
}
