package net.floodlightcontroller.core.util;

import net.floodlightcontroller.topology.TopologyManager;

public class UpdateScheduler implements Runnable {

	private TopologyManager myTp;
	
	public UpdateScheduler(TopologyManager tp)
	{
		myTp = tp;
	}
	
	@Override
	public void run() {
		// TODO Auto-generated method stub
		while(true)
		{
			try {
				Thread.sleep(3000);
				myTp.getCurrentInstance().calculateShortestPathTreeInClusters();
			} catch (InterruptedException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}

}
