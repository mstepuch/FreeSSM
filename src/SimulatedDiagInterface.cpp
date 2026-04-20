/*
 * SimulatedDiagInterface.cpp - Simulated diagnostic interface for UI testing without hardware
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

#include "SimulatedDiagInterface.h"
#include <cmath>
#include <cstring>

#ifdef __FSSM_DEBUG__
	#include <iostream>
#endif


// Simulated ECU identity: 2006 Subaru EJ253 2.5L SOHC
static const unsigned char SIM_SYS_ID[3] = { 0xA2, 0x10, 0x01 };
static const unsigned char SIM_ROM_ID[5] = { 0xA4, 0xF8, 0x12, 0x00, 0x01 };
static const int SIM_FLAGBYTES_COUNT = 96;


SimulatedDiagInterface::SimulatedDiagInterface()
{
	_open = false;
	_connected = false;
	_protocol = protocol_type::NONE;
	_readCounter = 0;
}


SimulatedDiagInterface::~SimulatedDiagInterface()
{
	disconnect();
	close();
}


AbstractDiagInterface::interface_type SimulatedDiagInterface::interfaceType()
{
	return interface_type::serialPassThrough; // Mimic serial pass-through for protocol compatibility
}


bool SimulatedDiagInterface::open( std::string name )
{
	if (_open)
		return false;
	_open = true;
	setName(name);
	setVersion("Sim 1.0");
	std::vector<protocol_type> protocols;
	protocols.push_back(protocol_type::SSM2_ISO14230);
	protocols.push_back(protocol_type::SSM2_ISO15765);
	protocols.push_back(protocol_type::SSM1);
	setSupportedProtocols(protocols);
#ifdef __FSSM_DEBUG__
	std::cout << "SimulatedDiagInterface::open():   opened simulated interface\n";
#endif
	return true;
}


bool SimulatedDiagInterface::isOpen()
{
	return _open;
}


bool SimulatedDiagInterface::close()
{
	if (!_open)
		return false;
	_open = false;
	_connected = false;
	_protocol = protocol_type::NONE;
	_responseBuffer.clear();
#ifdef __FSSM_DEBUG__
	std::cout << "SimulatedDiagInterface::close():   closed simulated interface\n";
#endif
	return true;
}


bool SimulatedDiagInterface::connect(AbstractDiagInterface::protocol_type protocol)
{
	if (!_open || _connected)
		return false;
	if (protocol == protocol_type::NONE)
		return false;
	_connected = true;
	_protocol = protocol;
	setProtocolType(protocol);
	if (protocol == protocol_type::SSM2_ISO14230)
		setProtocolBaudrate(4800);
	else if (protocol == protocol_type::SSM2_ISO15765)
		setProtocolBaudrate(500000);
	else
		setProtocolBaudrate(4800);
#ifdef __FSSM_DEBUG__
	std::cout << "SimulatedDiagInterface::connect():   connected with simulated protocol\n";
#endif
	return true;
}


bool SimulatedDiagInterface::isConnected()
{
	return _connected;
}


bool SimulatedDiagInterface::disconnect()
{
	if (!_connected)
		return false;
	_connected = false;
	_protocol = protocol_type::NONE;
	setProtocolType(protocol_type::NONE);
	_responseBuffer.clear();
	return true;
}


bool SimulatedDiagInterface::read(std::vector<char> *buffer)
{
	if (!_connected || !buffer)
		return false;
	if (_responseBuffer.empty())
		return false;
	*buffer = _responseBuffer;
	_responseBuffer.clear();
	return true;
}


bool SimulatedDiagInterface::write(std::vector<char> buffer)
{
	if (!_connected)
		return false;
	_responseBuffer.clear();
	buildSSM2response(buffer);
	return true;
}


bool SimulatedDiagInterface::clearSendBuffer()
{
	return true;
}


bool SimulatedDiagInterface::clearReceiveBuffer()
{
	_responseBuffer.clear();
	return true;
}


unsigned char SimulatedDiagInterface::calcChecksum(const std::vector<char> &data, size_t start, size_t count)
{
	unsigned int sum = 0;
	for (size_t i = start; i < start + count && i < data.size(); i++)
		sum += static_cast<unsigned char>(data[i]);
	return static_cast<unsigned char>(sum & 0xFF);
}


unsigned char SimulatedDiagInterface::simulateValue(unsigned int addr)
{
	_readCounter++;
	double t = _readCounter * 0.05; // simulated time progression

	switch (addr)
	{
		case 0x0E: // Engine Speed high byte: ~850 rpm idle, formula: (val*256+low)*0.25
			return static_cast<unsigned char>((3400 + static_cast<int>(200.0 * std::sin(t * 0.3))) >> 8);
		case 0x0F: // Engine Speed low byte
			return static_cast<unsigned char>((3400 + static_cast<int>(200.0 * std::sin(t * 0.3))) & 0xFF);
		case 0x08: // Coolant Temp: formula val-40, target ~80°C → raw 120
			return static_cast<unsigned char>(120 + static_cast<int>(2.0 * std::sin(t * 0.1)));
		case 0x07: // Engine Load: 0-255 range, idle ~20%
			return static_cast<unsigned char>(51 + static_cast<int>(10.0 * std::sin(t * 0.5)));
		case 0x10: // Vehicle Speed: 0 at idle
			return 0;
		case 0x11: // Ignition Timing: formula (val-128)*0.5, target ~15° → raw 158
			return static_cast<unsigned char>(158 + static_cast<int>(5.0 * std::sin(t * 0.7)));
		case 0x1C: // Battery Voltage: formula val*0.08, target 14.2V → raw 178
			return static_cast<unsigned char>(178 + static_cast<int>(3.0 * std::sin(t * 0.2)));
		case 0x12: // MAF Sensor Voltage high
			return static_cast<unsigned char>(1 + static_cast<int>(std::sin(t * 0.4) * 0.5));
		case 0x13: // MAF Sensor Voltage low
			return static_cast<unsigned char>(128 + static_cast<int>(60.0 * std::sin(t * 0.4)));
		case 0x09: // Intake Air Temp: formula val-40, target ~25°C → raw 65
			return 65;
		case 0x15: // Throttle Opening Angle: idle ~0
			return static_cast<unsigned char>(5 + static_cast<int>(3.0 * std::sin(t * 0.6)));
		case 0x46: // A/F sensor #1: formula val/128, target ~1.0 → raw 128
			return static_cast<unsigned char>(128 + static_cast<int>(5.0 * std::sin(t * 0.8)));
		case 0x62: // Ignition switch state: bit 3 must be set for ignition ON
			return 0x08;
		default:
			// Generic oscillating value for any unmapped address
			return static_cast<unsigned char>(128 + static_cast<int>(100.0 * std::sin(t + addr * 0.37)));
	}
}


void SimulatedDiagInterface::buildSSM2response(const std::vector<char> &request)
{
	if (_protocol == protocol_type::SSM2_ISO14230)
	{
		// K-Line packet: 80 [dst] [src] [len] [payload...] [chk]
		if (request.size() < 6)
			return;
		if (static_cast<unsigned char>(request[0]) != 0x80)
			return;

		unsigned char ecuAddr = static_cast<unsigned char>(request[1]);
		unsigned char payloadLen = static_cast<unsigned char>(request[3]);
		if (request.size() < static_cast<size_t>(4 + payloadLen + 1))
			return;

		unsigned char cmd = static_cast<unsigned char>(request[4]);

		if (cmd == 0xBF) // GetCUdata
		{
			// Response: 80 F0 [ecuAddr] [len] FF [SYS_ID 3] [ROM_ID 5] [flagbytes 96] [chk]
			unsigned char respPayloadLen = 1 + 3 + 5 + SIM_FLAGBYTES_COUNT; // 105
			_responseBuffer.clear();
			_responseBuffer.push_back(static_cast<char>(0x80));       // header
			_responseBuffer.push_back(static_cast<char>(0xF0));       // dest = tester
			_responseBuffer.push_back(static_cast<char>(ecuAddr));    // src = ECU
			_responseBuffer.push_back(static_cast<char>(respPayloadLen));
			_responseBuffer.push_back(static_cast<char>(0xFF));       // response cmd
			for (int i = 0; i < 3; i++)
				_responseBuffer.push_back(static_cast<char>(SIM_SYS_ID[i]));
			for (int i = 0; i < 5; i++)
				_responseBuffer.push_back(static_cast<char>(SIM_ROM_ID[i]));
			for (int i = 0; i < SIM_FLAGBYTES_COUNT; i++)
				_responseBuffer.push_back(static_cast<char>(0xFF));   // all features enabled
			unsigned char chk = calcChecksum(_responseBuffer, 0, _responseBuffer.size());
			_responseBuffer.push_back(static_cast<char>(chk));
		}
		else if (cmd == 0xA8) // ReadMultipleDatabytes
		{
			// Request payload: A8 [pad] [addr1_hi addr1_mid addr1_lo] [addr2...] ...
			if (payloadLen < 5)
				return;
			int numAddresses = (payloadLen - 2) / 3; // subtract cmd and pad byte
			_responseBuffer.clear();
			_responseBuffer.push_back(static_cast<char>(0x80));
			_responseBuffer.push_back(static_cast<char>(0xF0));
			_responseBuffer.push_back(static_cast<char>(ecuAddr));
			_responseBuffer.push_back(static_cast<char>(numAddresses + 1)); // payload len
			_responseBuffer.push_back(static_cast<char>(0xE8));             // response cmd
			for (int i = 0; i < numAddresses; i++)
			{
				int offset = 5 + 1 + i * 3; // skip header(4) + cmd(1) + pad(1)
				unsigned int addr = (static_cast<unsigned char>(request[offset]) << 16)
				                  | (static_cast<unsigned char>(request[offset + 1]) << 8)
				                  | static_cast<unsigned char>(request[offset + 2]);
				_responseBuffer.push_back(static_cast<char>(simulateValue(addr)));
			}
			unsigned char chk = calcChecksum(_responseBuffer, 0, _responseBuffer.size());
			_responseBuffer.push_back(static_cast<char>(chk));
		}
		else if (cmd == 0xA0) // ReadDataBlock
		{
			// Request payload: A0 [pad] [addr_hi addr_mid addr_lo] [count-1]
			if (payloadLen < 6)
				return;
			unsigned int startAddr = (static_cast<unsigned char>(request[6]) << 16)
			                       | (static_cast<unsigned char>(request[7]) << 8)
			                       | static_cast<unsigned char>(request[8]);
			int count = static_cast<unsigned char>(request[9]) + 1;
			_responseBuffer.clear();
			_responseBuffer.push_back(static_cast<char>(0x80));
			_responseBuffer.push_back(static_cast<char>(0xF0));
			_responseBuffer.push_back(static_cast<char>(ecuAddr));
			_responseBuffer.push_back(static_cast<char>(count + 1)); // payload len
			_responseBuffer.push_back(static_cast<char>(0xE0));      // response cmd
			for (int i = 0; i < count; i++)
				_responseBuffer.push_back(static_cast<char>(simulateValue(startAddr + i)));
			unsigned char chk = calcChecksum(_responseBuffer, 0, _responseBuffer.size());
			_responseBuffer.push_back(static_cast<char>(chk));
		}
		else if (cmd == 0xB8) // WriteDatabyte
		{
			// Response: echo back the written value
			if (payloadLen < 5)
				return;
			unsigned char writtenVal = static_cast<unsigned char>(request[8]);
			_responseBuffer.clear();
			_responseBuffer.push_back(static_cast<char>(0x80));
			_responseBuffer.push_back(static_cast<char>(0xF0));
			_responseBuffer.push_back(static_cast<char>(ecuAddr));
			_responseBuffer.push_back(static_cast<char>(2));         // payload len
			_responseBuffer.push_back(static_cast<char>(0xF8));      // response cmd
			_responseBuffer.push_back(static_cast<char>(writtenVal));
			unsigned char chk = calcChecksum(_responseBuffer, 0, _responseBuffer.size());
			_responseBuffer.push_back(static_cast<char>(chk));
		}
	}
	else if (_protocol == protocol_type::SSM2_ISO15765)
	{
		// CAN packet: [CAN_ID 4 bytes BE] [payload]
		if (request.size() < 5)
			return;

		unsigned char cmd = static_cast<unsigned char>(request[4]);

		if (cmd == 0xBF || cmd == 0xAA) // GetCUdata
		{
			unsigned char respCmd = (cmd == 0xBF) ? 0xFF : 0xEA;
			_responseBuffer.clear();
			// CAN response ID = request ID + 8
			unsigned int reqID = (static_cast<unsigned char>(request[0]) << 24)
			                   | (static_cast<unsigned char>(request[1]) << 16)
			                   | (static_cast<unsigned char>(request[2]) << 8)
			                   | static_cast<unsigned char>(request[3]);
			unsigned int respID = reqID + 8;
			_responseBuffer.push_back(static_cast<char>((respID >> 24) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 16) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 8) & 0xFF));
			_responseBuffer.push_back(static_cast<char>(respID & 0xFF));
			_responseBuffer.push_back(static_cast<char>(respCmd));
			for (int i = 0; i < 3; i++)
				_responseBuffer.push_back(static_cast<char>(SIM_SYS_ID[i]));
			for (int i = 0; i < 5; i++)
				_responseBuffer.push_back(static_cast<char>(SIM_ROM_ID[i]));
			for (int i = 0; i < SIM_FLAGBYTES_COUNT; i++)
				_responseBuffer.push_back(static_cast<char>(0xFF));
		}
		else if (cmd == 0xA8) // ReadMultipleDatabytes
		{
			int numAddresses = (static_cast<int>(request.size()) - 4 - 2) / 3;
			_responseBuffer.clear();
			unsigned int reqID = (static_cast<unsigned char>(request[0]) << 24)
			                   | (static_cast<unsigned char>(request[1]) << 16)
			                   | (static_cast<unsigned char>(request[2]) << 8)
			                   | static_cast<unsigned char>(request[3]);
			unsigned int respID = reqID + 8;
			_responseBuffer.push_back(static_cast<char>((respID >> 24) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 16) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 8) & 0xFF));
			_responseBuffer.push_back(static_cast<char>(respID & 0xFF));
			_responseBuffer.push_back(static_cast<char>(0xE8));
			for (int i = 0; i < numAddresses; i++)
			{
				int offset = 4 + 2 + i * 3; // CAN_ID(4) + cmd(1) + pad(1)
				unsigned int addr = (static_cast<unsigned char>(request[offset]) << 16)
				                  | (static_cast<unsigned char>(request[offset + 1]) << 8)
				                  | static_cast<unsigned char>(request[offset + 2]);
				_responseBuffer.push_back(static_cast<char>(simulateValue(addr)));
			}
		}
		else if (cmd == 0xA0) // ReadDataBlock
		{
			unsigned int startAddr = (static_cast<unsigned char>(request[6]) << 16)
			                       | (static_cast<unsigned char>(request[7]) << 8)
			                       | static_cast<unsigned char>(request[8]);
			int count = static_cast<unsigned char>(request[9]) + 1;
			_responseBuffer.clear();
			unsigned int reqID = (static_cast<unsigned char>(request[0]) << 24)
			                   | (static_cast<unsigned char>(request[1]) << 16)
			                   | (static_cast<unsigned char>(request[2]) << 8)
			                   | static_cast<unsigned char>(request[3]);
			unsigned int respID = reqID + 8;
			_responseBuffer.push_back(static_cast<char>((respID >> 24) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 16) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 8) & 0xFF));
			_responseBuffer.push_back(static_cast<char>(respID & 0xFF));
			_responseBuffer.push_back(static_cast<char>(0xE0));
			for (int i = 0; i < count; i++)
				_responseBuffer.push_back(static_cast<char>(simulateValue(startAddr + i)));
		}
		else if (cmd == 0xB8) // WriteDatabyte
		{
			unsigned char writtenVal = static_cast<unsigned char>(request[8]);
			_responseBuffer.clear();
			unsigned int reqID = (static_cast<unsigned char>(request[0]) << 24)
			                   | (static_cast<unsigned char>(request[1]) << 16)
			                   | (static_cast<unsigned char>(request[2]) << 8)
			                   | static_cast<unsigned char>(request[3]);
			unsigned int respID = reqID + 8;
			_responseBuffer.push_back(static_cast<char>((respID >> 24) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 16) & 0xFF));
			_responseBuffer.push_back(static_cast<char>((respID >> 8) & 0xFF));
			_responseBuffer.push_back(static_cast<char>(respID & 0xFF));
			_responseBuffer.push_back(static_cast<char>(0xF8));
			_responseBuffer.push_back(static_cast<char>(writtenVal));
		}
	}
}
