/*
 * SimulatedDiagInterface.h - Simulated diagnostic interface for UI testing without hardware
 *
 * Copyright (C) 2026 mstepuch (FreeSSM fork)
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

#ifndef SIMULATEDDIAGINTERFACE_H
#define SIMULATEDDIAGINTERFACE_H


#include "AbstractDiagInterface.h"
#include <vector>
#include <string>


class SimulatedDiagInterface : public AbstractDiagInterface
{

public:
	SimulatedDiagInterface();
	~SimulatedDiagInterface();
	interface_type interfaceType();
	bool open( std::string name );
	bool isOpen();
	bool close();
	bool connect(AbstractDiagInterface::protocol_type protocol);
	bool isConnected();
	bool disconnect();
	bool read(std::vector<char> *buffer);
	bool write(std::vector<char> buffer);
	bool clearSendBuffer();
	bool clearReceiveBuffer();

private:
	bool _open;
	bool _connected;
	protocol_type _protocol;
	std::vector<char> _responseBuffer;
	unsigned int _readCounter;

	void buildSSM2response(const std::vector<char> &request);
	unsigned char simulateValue(unsigned int addr);
	static unsigned char calcChecksum(const std::vector<char> &data, size_t start, size_t count);

};


#endif
