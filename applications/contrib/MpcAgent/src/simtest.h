#ifndef _simtest_h_
#define _simtest_h_
#include <iostream>
#include <fstream>
#include "adevs.h"
#include "building.h"
#include "control.h"

/**
 * This header file defines the structure of a simulation
 * test harness for the control code. It includes a simulated
 * building and a driver for controls that implement the
 * Control interface.
 */

/// Types of equipment in a building
enum EquipmentType
{
	NONE,
	HEATING_UNIT,
	COOLING_UNIT,
	THERMOSTAT_UPPER_SETPOINT,
	THERMOSTAT_LOWER_SETPOINT,
	THERMOSTAT_THERMOMETER,
	OUTDOOR_THERMOMETER
};

/**
 * An event acting or generated by a piece of building equipment.
 */
class BuildingEvent
{
	public:
		/**
		 * Unit numbers should be from 0 to N-1 when there are N
		 * instances of a particular type of equipment.
		 */
		BuildingEvent(EquipmentType item = NONE, int unitNumber = -1):
			item(item),unit(unitNumber){}
		int getUnit() const { return unit; }
		EquipmentType getItem() const { return item; }
		virtual ~BuildingEvent(){}
	private:
		EquipmentType item;
		int unit;
};

class OnOffEvent:
	public BuildingEvent
{
	public:
		/**
		 * A piece of equipment was turned on or turned off.
		 */
		OnOffEvent(EquipmentType item, int unitNumber, bool isOn):
			BuildingEvent(item,unitNumber),mode((int)isOn){}
		/**
		 * Use mode = 0 for off. Anything else is on though models may
		 * react differently to separate mode settings.
		 */
		OnOffEvent(EquipmentType item, int unitNumber, int mode):
			BuildingEvent(item,unitNumber),mode(mode){}
		bool isOn() const { return (mode != 0); }
		bool isOff() const { return (mode == 0); }
		int getMode() const { return mode; }
	private:
		int mode;
};

class TemperatureEvent:
	public BuildingEvent
{
	public:
		/**
		 * A piece of equipment is reporting a new temperature reading.
		 */
		TemperatureEvent(EquipmentType item, int unitNumber, double degC):
			BuildingEvent(item,unitNumber),degC(degC){}
		double getTempC() const { return degC; }
	private:
		double degC;
};

typedef adevs::Bag<adevs::PortValue<BuildingEvent*> > IO_Bag;

class AtomicModel:
	public adevs::Atomic<adevs::PortValue<BuildingEvent*> >
{
	public:
		void gc_output(IO_Bag& g)
		{
			IO_Bag::iterator iter = g.begin();
			for (; iter != g.end(); iter++)
				delete (*iter).value;
		}
};

/**
 * This is a partial implementation of a building proxy that
 * manages events for the simulation system. Derived classes
 * will implement a proxy for a specific building.
 */
class SimulatedBuildingProxy:
	public BuildingProxy
{
	public:
		/// Constructor
		SimulatedBuildingProxy();
		/// Destructor
		virtual ~SimulatedBuildingProxy();
		/**
		 * These methods must be supplied by the simulator. They will be
		 * called upon receipt of an event from the dynamic model of the
		 * building to set the appropriate zone values.
		 */
		/// Set the outdoor air temperature in degrees Celcius
		virtual void setOutdoorTemp(double degC) = 0;
		/// Set the thermostat temperature zone in degrees Celcius
		virtual void setThermostatTemp(int zone, double degC) = 0;
		/// Read the thermostat setpoint in degrees Celcius
		virtual void setThermostatUpperLimit(int zone, double degC) = 0;
		virtual void setThermostatLowerLimit(int zone, double degC) = 0;
		/**
		 * These methods put events into the pending event set.
		 * When overriding this method, make sure to call the
		 * method of the base class if the action should actually
		 * take place.
		 */ 
		virtual void activateCoolingUnit(int unit, int stage);
		virtual void activateHeatingUnit(int unit, int stage);
		/**
		 * These methods are for event handling by the simulator.
		 */
		// Copy pending events to the supplied bag
		void getPendingEvents(IO_Bag& pending);
		// Clear the pending events list
		void clearPendingEvents() { pendingEvents.clear(); }
		// Are there pending events?
		bool hasPendingEvents() { return !pendingEvents.empty(); }
	private:
		std::list<adevs::PortValue<BuildingEvent*> > pendingEvents;
};

/**
 * Generates sampling events for the dynamic building model
 * at rate indicated by the controller.
 */
class SampleClock:
	public AtomicModel
{
	public:
		static const int sample;

		SampleClock(double freq):
			AtomicModel(),first(0.0),freq(freq){}
		double ta() { return first*(1.0/freq); }
		void delta_int() { first = 1.0; }
		void delta_ext(double,const IO_Bag&){}
		void delta_conf(const IO_Bag&){}
		void output_func(IO_Bag& yb)
		{
			adevs::PortValue<BuildingEvent*> pv;
			pv.port = sample;
			pv.value = new BuildingEvent();
			yb.insert(pv);
		}
	private:
		double first;
		const double freq;
};

/**
 * Wrapper around the control model and its simulated building.
 */
class ControlHarness:
	public AtomicModel
{
	public:
		/**
		 * Input port for receiving new temperature data. Objects
		 * on this port must be of type TemperatureEvent and these
		 * will cause a change in the appropriate temperature data
		 * of the building proxy.
		 */
		static const int tempData;
		/**
		 * This output port generates OnOffEvent objects to 
		 * activate or deactive building equipment.
		 */
		static const int onOffCmd;
		/**
		 * This outport port generates a request for a sample at every
		 * sampling instant for the control.
		 */
		static const int sample;

		ControlHarness(Control* control, SimulatedBuildingProxy* bldg);
		double ta();
		void delta_int();
		void delta_ext(double e, const IO_Bag& xb);
		void delta_conf(const IO_Bag& xb);
		void output_func(IO_Bag& yb);
	private:
		Control* control;
		SimulatedBuildingProxy* bldg;
		double t_left;
		bool run_control; 
};

/**
 * DEVS interface that must be exported by any dynamic
 * model of the building.
 */
class BuildingModelInterface
{
	public:
		/**
		 * Request for a sample. The object on this port
		 * will be a BuildingEvent and the model should update it variables
		 * and generate appropriate output immediately.
		 */
		static const int sample;
		/**
		 * Output on this port must be of type TemperatureEvent
		 * and should report new temperature data for any 
		 * equipment.
		 */
		static const int tempData;
		/**
		 * This input port receives OnOffEvent objects to 
		 * activate or deactive building equipment.
		 */
		static const int onOffCmd;

		virtual std::string getState() = 0;
		virtual ~BuildingModelInterface(){}
};

/**
 * Constructs the complete test model.
 */
class TestModel:
	public adevs::Digraph<BuildingEvent*>
{
	public:
		/// All objects are destroyed when the test model is destroyed
		TestModel
		(
			Control* control,
			SimulatedBuildingProxy* bldgProxy,
			// Must implement BuildingModelInterface
			adevs::Devs<adevs::PortValue<BuildingEvent*> >* bldgModel
		);
		/// Write the model state to cntrl.dat, bldgp.dat, and bldgm.dat
		void print_state(double simTime);
		~TestModel();
	private:
		BuildingModelInterface* bldgModelI;
		SimulatedBuildingProxy* bldgProxy;
		Control* control;
		std::ofstream bldgModelOut;
		std::ofstream bldgProxyOut;
		std::ofstream cntrlOut;
};

#endif
