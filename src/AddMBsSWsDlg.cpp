/*
 * AddMBsSWsDlg.cpp - Dialog for selecting/adding measuring blocks and switches
 *
 * Copyright (C) 2008-2018 Comer352L
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "AddMBsSWsDlg.h"

#include <numeric>
#include <QKeyEvent>
#include <QMouseEvent>
#include <QBoxLayout>
#include <QHeaderView>



AddMBsSWsDlg::AddMBsSWsDlg(QWidget *parent, std::vector<mb_dt> supportedMBs, std::vector<sw_dt> supportedSWs,
                           std::vector<MBSWmetadata_dt> *MBSWmetaList) : QDialog(parent)
{
	bool unselected = false;
	MBSWmetadata_dt tmpMBSWmd;

	_MBSWmetaList = MBSWmetaList;
	_unselectedMBsSWs_metaList.clear();
	_selectionAnchorRow = -1;
	// Setup GUI:
	setupUi(this);
	// Insert search box above the table.
	_searchEdit = new QLineEdit(this);
	_searchEdit->setPlaceholderText(tr("Search (e.g. solenoid, EVAP, temperature)..."));
	_searchEdit->setClearButtonEnabled(true);
	if (QBoxLayout* boxLayout = qobject_cast<QBoxLayout*>(MBsSWs_tableWidget->parentWidget()->layout()))
	{
		const int tableIndex = boxLayout->indexOf(MBsSWs_tableWidget);
		boxLayout->insertWidget(tableIndex >= 0 ? tableIndex : 0, _searchEdit);
	}
	else if (QGridLayout* gridLayout = qobject_cast<QGridLayout*>(MBsSWs_tableWidget->parentWidget()->layout()))
	{
		// Fallback for small-resolution UI (QGridLayout): push the table down by one row.
		const int rows = gridLayout->rowCount();
		for (int r = rows - 1; r >= 0; --r)
		{
			for (int c = 0; c < gridLayout->columnCount(); ++c)
			{
				QLayoutItem* it = gridLayout->itemAtPosition(r, c);
				if (!it) continue;
				QWidget* w = it->widget();
				if (!w) continue;
				int fr, fc, rs, cs;
				gridLayout->getItemPosition(gridLayout->indexOf(w), &fr, &fc, &rs, &cs);
				gridLayout->removeWidget(w);
				gridLayout->addWidget(w, fr + 1, fc, rs, cs);
			}
		}
		gridLayout->addWidget(_searchEdit, 0, 0, 1, gridLayout->columnCount() > 0 ? gridLayout->columnCount() : 1);
	}
	// Click without modifiers keeps previous selection (MultiSelection);
	// Shift+click is handled manually in eventFilter() to produce a range selection.
	MBsSWs_tableWidget->setSelectionBehavior(QAbstractItemView::SelectRows);
	MBsSWs_tableWidget->setSelectionMode(QAbstractItemView::MultiSelection);
	MBsSWs_tableWidget->viewport()->installEventFilter(this);
	// enable maximize and minimize buttons
	//   GNOME 3 at least: this also enables fast window management e.g. "View split on left" (Super-Left), "... right" (Super-Right)
	setWindowFlags( Qt::Window );

	iconMB = QIcon(":/icons/freessm/32x32/MB.png");
	iconSW = QIcon(":/icons/freessm/32x32/SW.png");
	QHeaderView* headerview = MBsSWs_tableWidget->horizontalHeader();
#if QT_VERSION < 0x050000
	headerview->setResizeMode(static_cast<int>(Column::type), QHeaderView::ResizeToContents);
	headerview->setResizeMode(static_cast<int>(Column::title), QHeaderView::Stretch);
	headerview->setResizeMode(static_cast<int>(Column::unit), QHeaderView::ResizeToContents);
#else
	headerview->setSectionResizeMode(static_cast<int>(Column::type), QHeaderView::ResizeToContents);
	headerview->setSectionResizeMode(static_cast<int>(Column::title), QHeaderView::Stretch);
	headerview->setSectionResizeMode(static_cast<int>(Column::unit), QHeaderView::ResizeToContents);
#endif
	// Set table row resize behavior:
	headerview = MBsSWs_tableWidget->verticalHeader();
#if QT_VERSION < 0x050000
	headerview->setResizeMode(QHeaderView::Fixed);
#else
	headerview->setSectionResizeMode(QHeaderView::Fixed);
#endif

	std::vector<Item> items;
	// FIND AVAILABLE (UNSELECTED) MBs:
	tmpMBSWmd.blockType = BlockType::MB;
	for (size_t k = 0; k < supportedMBs.size(); ++k)
	{
		unselected = true;
		for (size_t m = 0; m < _MBSWmetaList->size(); ++m)
		{
			const MBSWmetadata_dt& metadata = _MBSWmetaList->at(m);
			if (metadata.blockType == BlockType::MB && metadata.nativeIndex == k)
			{
				unselected = false;
				break;
			}
		}
		if (unselected)
		{
			const mb_dt& mb = supportedMBs.at(k);
			// Output MB:
			items.push_back(Item { BlockType::MB, mb.title, mb.unit });

			// Put MB to the list of unselected MBs/SWs:
			tmpMBSWmd.nativeIndex = k;
			_unselectedMBsSWs_metaList.push_back( tmpMBSWmd );
		}
	}
	// FIND AVAILABLE (UNSELECTED) SWs:
	tmpMBSWmd.blockType = BlockType::SW;
	for (size_t k=0; k < supportedSWs.size(); ++k)
	{
		unselected = true;
		for (size_t m = 0; m < _MBSWmetaList->size(); ++m)
		{
			const MBSWmetadata_dt& metadata = _MBSWmetaList->at(m);
			if (metadata.blockType == BlockType::SW && metadata.nativeIndex == k)
			{
				unselected = false;
				break;
			}
		}
		if (unselected)
		{
			// Output SW:
			sw_dt& sw = supportedSWs.at(k);
			items.push_back(Item { BlockType::SW, sw.title, sw.unit.replace('\\','/') });

			// Put SW to the list of unselected MBs/SWs:
			tmpMBSWmd.nativeIndex = k;
			_unselectedMBsSWs_metaList.push_back( tmpMBSWmd );
		}
	}

	// Sort available entries alphabetically by title while keeping metadata mapping intact.
	if (items.size() == _unselectedMBsSWs_metaList.size() && items.size() > 1)
	{
		std::vector<size_t> sortedIndexes(items.size());
		std::iota(sortedIndexes.begin(), sortedIndexes.end(), 0);
		std::stable_sort(sortedIndexes.begin(), sortedIndexes.end(), [&items](size_t a, size_t b)
		{
			const QString titleA = items.at(a).title.toLower();
			const QString titleB = items.at(b).title.toLower();
			return QString::localeAwareCompare(titleA, titleB) < 0;
		});

		std::vector<Item> sortedItems;
		std::vector<MBSWmetadata_dt> sortedMetadata;
		sortedItems.reserve(items.size());
		sortedMetadata.reserve(_unselectedMBsSWs_metaList.size());

		for (size_t index : sortedIndexes)
		{
			sortedItems.push_back(items.at(index));
			sortedMetadata.push_back(_unselectedMBsSWs_metaList.at(index));
		}

		items.swap(sortedItems);
		_unselectedMBsSWs_metaList.swap(sortedMetadata);
	}

	_allItems = items;
	_visibleToAllIndex.resize(_allItems.size());
	std::iota(_visibleToAllIndex.begin(), _visibleToAllIndex.end(), 0);
	setContent(items);
	// Enable/disable "Add" button:
	setAddButtonEnableStatus();
	// CONNECT BUTTONS AND LIST WIDGET WITH SLOTS:
	connect(add_pushButton, SIGNAL( released() ), this, SLOT( add() ));
	connect(cancel_pushButton, SIGNAL( released() ), this, SLOT( cancel() ));
	connect(MBsSWs_tableWidget, SIGNAL( itemSelectionChanged() ), this, SLOT( setAddButtonEnableStatus() ));
	connect(_searchEdit, SIGNAL( textChanged(QString) ), this, SLOT( applyFilter(QString) ));
	_searchEdit->setFocus();
}


AddMBsSWsDlg::~AddMBsSWsDlg()
{
	disconnect(add_pushButton, SIGNAL( released() ), this, SLOT( add() ));
	disconnect(cancel_pushButton, SIGNAL( released() ), this, SLOT( cancel() ));
	disconnect(MBsSWs_tableWidget, SIGNAL( itemSelectionChanged() ), this, SLOT( setAddButtonEnableStatus() ));
	disconnect(_searchEdit, SIGNAL( textChanged(QString) ), this, SLOT( applyFilter(QString) ));
}


void AddMBsSWsDlg::add()
{
	disconnect(add_pushButton, SIGNAL( pressed() ), this, SLOT( add() )); // bugfix !
	QItemSelectionModel *selModel = MBsSWs_tableWidget->selectionModel();
	QModelIndexList MIlist = selModel->selectedRows();
	std::sort(MIlist.begin(), MIlist.end(), rowIndexLessThan);	// since Qt 4.4.1, we have to sort the QModelIndexes...
	std::vector<int> metaIndexes;
	metaIndexes.reserve(MIlist.size());
	for (const QModelIndex& mi : MIlist)
	{
		const int visibleRow = mi.row();
		if (visibleRow < 0 || visibleRow >= (int)_visibleToAllIndex.size())
			continue;
		const int metaIdx = _visibleToAllIndex.at(visibleRow);
		if (metaIdx < 0 || metaIdx >= (int)_unselectedMBsSWs_metaList.size())
			continue;
		metaIndexes.push_back(metaIdx);
	}
	std::sort(metaIndexes.begin(), metaIndexes.end());
	for (int idx : metaIndexes)
		_MBSWmetaList->push_back( _unselectedMBsSWs_metaList.at(idx) );
	close();
}


void AddMBsSWsDlg::cancel()
{
	close();
}


void AddMBsSWsDlg::setAddButtonEnableStatus()
{
	const QList<QTableWidgetItem*> selitemslist = MBsSWs_tableWidget->selectedItems();
	// NOTE: returns the nr. of selected cells, NOT THE NR. OF ROWS ! Empty cells are not included !
	add_pushButton->setEnabled(selitemslist.size() > 0);
}


bool AddMBsSWsDlg::rowIndexLessThan(const QModelIndex mi_A, const QModelIndex mi_B)
{
	return mi_A.row() < mi_B.row();
}


void AddMBsSWsDlg::setContent(const std::vector<Item>& items)
{
	MBsSWs_tableWidget->clearContents();
	const size_t count = items.size();
	MBsSWs_tableWidget->setRowCount(count);

	for (size_t row = 0; row < count; ++row)
	{
		const Item& item = items.at(row);
		QTableWidgetItem* tableelement;

		const QIcon& icon = item.blockType == BlockType::MB ? iconMB : iconSW;
		tableelement = new QTableWidgetItem(icon, nullptr);
		MBsSWs_tableWidget->setItem(row, static_cast<int>(Column::type), tableelement);

		tableelement = new QTableWidgetItem(item.title);
		//tableelement->setTextAlignment(alignment);
		MBsSWs_tableWidget->setItem(row, static_cast<int>(Column::title), tableelement);

		tableelement = new QTableWidgetItem(item.unit);
		//tableelement->setTextAlignment(alignment);
		MBsSWs_tableWidget->setItem(row, static_cast<int>(Column::unit), tableelement);
	}
}


void AddMBsSWsDlg::applyFilter(const QString& text)
{
	const QString needle = text.trimmed();
	std::vector<Item> visible;
	_visibleToAllIndex.clear();
	visible.reserve(_allItems.size());
	_visibleToAllIndex.reserve(_allItems.size());
	for (size_t i = 0; i < _allItems.size(); ++i)
	{
		const Item& it = _allItems.at(i);
		if (needle.isEmpty() || it.title.contains(needle, Qt::CaseInsensitive)
		                     || it.unit.contains(needle, Qt::CaseInsensitive))
		{
			visible.push_back(it);
			_visibleToAllIndex.push_back(static_cast<int>(i));
		}
	}
	_selectionAnchorRow = -1;
	setContent(visible);
	setAddButtonEnableStatus();
}


bool AddMBsSWsDlg::eventFilter(QObject *obj, QEvent *event)
{
	if (obj == MBsSWs_tableWidget->viewport() && event->type() == QEvent::MouseButtonPress)
	{
		QMouseEvent *me = static_cast<QMouseEvent*>(event);
		if (me->button() == Qt::LeftButton)
		{
			const int row = MBsSWs_tableWidget->indexAt(me->pos()).row();
			if (row >= 0 && (me->modifiers() & Qt::ShiftModifier) && _selectionAnchorRow >= 0)
			{
				const int from = std::min(_selectionAnchorRow, row);
				const int to   = std::max(_selectionAnchorRow, row);
				QTableWidgetSelectionRange range(from, 0, to, MBsSWs_tableWidget->columnCount() - 1);
				MBsSWs_tableWidget->setRangeSelected(range, true);
				return true; // swallow: don't let MultiSelection toggle the clicked row
			}
			if (row >= 0)
				_selectionAnchorRow = row;
		}
	}
	return QDialog::eventFilter(obj, event);
}
