/********************************************************************************
** Form generated from reading UI file 'widget.ui'
**
** Created by: Qt User Interface Compiler version 6.6.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_WIDGET_H
#define UI_WIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QListView>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Widget
{
public:
    QLineEdit *IPLine;
    QLineEdit *PortLine;
    QLabel *LabelIP;
    QLabel *LabelPort;
    QPushButton *GetBtn;
    QListView *MessageList;
    QPushButton *SendBtn;
    QPushButton *ChangeModeBtn;
    QLineEdit *FileLine;
    QLabel *LabelFile;
    QLabel *ModeLabel;
    QPushButton *ClearBtn;

    void setupUi(QWidget *Widget)
    {
        if (Widget->objectName().isEmpty())
            Widget->setObjectName("Widget");
        Widget->resize(855, 600);
        IPLine = new QLineEdit(Widget);
        IPLine->setObjectName("IPLine");
        IPLine->setGeometry(QRect(130, 70, 221, 31));
        PortLine = new QLineEdit(Widget);
        PortLine->setObjectName("PortLine");
        PortLine->setGeometry(QRect(130, 130, 221, 31));
        LabelIP = new QLabel(Widget);
        LabelIP->setObjectName("LabelIP");
        LabelIP->setGeometry(QRect(20, 80, 101, 18));
        LabelPort = new QLabel(Widget);
        LabelPort->setObjectName("LabelPort");
        LabelPort->setGeometry(QRect(10, 130, 121, 18));
        GetBtn = new QPushButton(Widget);
        GetBtn->setObjectName("GetBtn");
        GetBtn->setGeometry(QRect(380, 70, 112, 34));
        MessageList = new QListView(Widget);
        MessageList->setObjectName("MessageList");
        MessageList->setGeometry(QRect(30, 190, 791, 381));
        SendBtn = new QPushButton(Widget);
        SendBtn->setObjectName("SendBtn");
        SendBtn->setGeometry(QRect(380, 130, 112, 34));
        ChangeModeBtn = new QPushButton(Widget);
        ChangeModeBtn->setObjectName("ChangeModeBtn");
        ChangeModeBtn->setGeometry(QRect(510, 70, 112, 34));
        FileLine = new QLineEdit(Widget);
        FileLine->setObjectName("FileLine");
        FileLine->setGeometry(QRect(130, 20, 591, 31));
        LabelFile = new QLabel(Widget);
        LabelFile->setObjectName("LabelFile");
        LabelFile->setGeometry(QRect(30, 20, 81, 18));
        ModeLabel = new QLabel(Widget);
        ModeLabel->setObjectName("ModeLabel");
        ModeLabel->setGeometry(QRect(640, 80, 201, 16));
        QFont font;
        font.setPointSize(12);
        ModeLabel->setFont(font);
        ClearBtn = new QPushButton(Widget);
        ClearBtn->setObjectName("ClearBtn");
        ClearBtn->setGeometry(QRect(510, 130, 112, 34));

        retranslateUi(Widget);

        QMetaObject::connectSlotsByName(Widget);
    } // setupUi

    void retranslateUi(QWidget *Widget)
    {
        Widget->setWindowTitle(QCoreApplication::translate("Widget", "Widget", nullptr));
        IPLine->setText(QCoreApplication::translate("Widget", "10.12.174.1", nullptr));
        PortLine->setText(QCoreApplication::translate("Widget", "69", nullptr));
        LabelIP->setText(QCoreApplication::translate("Widget", "Server IP:", nullptr));
        LabelPort->setText(QCoreApplication::translate("Widget", "Server Port:", nullptr));
        GetBtn->setText(QCoreApplication::translate("Widget", "Get", nullptr));
        SendBtn->setText(QCoreApplication::translate("Widget", "Send", nullptr));
        ChangeModeBtn->setText(QCoreApplication::translate("Widget", "Change Mode", nullptr));
        LabelFile->setText(QCoreApplication::translate("Widget", "File:", nullptr));
        ModeLabel->setText(QCoreApplication::translate("Widget", "Current Mode: octet", nullptr));
        ClearBtn->setText(QCoreApplication::translate("Widget", "Clear", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Widget: public Ui_Widget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_WIDGET_H
