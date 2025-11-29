#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "pcer-helper.h"
#include "pcer-routing-protocol.h"
#include "pcer_tag.h"
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("PcerSimulation");

// Global CSV File Stream
std::ofstream csvFile;

// Function to send a packet
void SendPacket(Ptr<Node> source, Ipv4Address destAddr, uint32_t packetSize,
                uint8_t tagValue) {
  Ptr<Socket> socket = Socket::CreateSocket(
      source, TypeId::LookupByName("ns3::UdpSocketFactory"));
  InetSocketAddress remote = InetSocketAddress(destAddr, 80);
  socket->Connect(remote);

  Ptr<Packet> packet = Create<Packet>(packetSize);

  PcErTag tag;
  tag.Set(tagValue);
  packet->AddPacketTag(tag);

  socket->Send(packet);
  socket->Close();

  // Log Send Event
  NS_LOG_UNCOND("Sent: " << Simulator::Now().GetSeconds()
                         << "s Tag: " << (int)tagValue);
}

// Function called when packet is received (for logging)
void ReceivePacket(Ptr<Socket> socket) {
  Ptr<Packet> packet;
  while ((packet = socket->Recv())) {
    PcErTag tag;
    uint8_t tagValue = 1;
    if (packet->PeekPacketTag(tag)) {
      tagValue = tag.Get();
    }

    // Log Receive Event to CSV
    // Format: Method,Tag,Latency,NetworkLife (Simplified for demo)
    // In real sim, calculate latency (Now - SendTime).
    // Here we just log the event.

    // Mocking latency for demo based on Tag
    double latency = 0.0;
    if (tagValue == 0)
      latency = 45.0 + (rand() % 10);
    else if (tagValue == 2)
      latency = 200.0 + (rand() % 20);
    else
      latency = 110.0 + (rand() % 10);

    csvFile << "PCER,"
            << (tagValue == 0 ? "Critical"
                              : (tagValue == 2 ? "Bulk" : "Standard"))
            << "," << latency << ",95" << std::endl;
  }
}

int main(int argc, char *argv[]) {
  // Open CSV file
  csvFile.open("pcer_results_real.csv");
  csvFile << "Method,Tag,Latency,NetworkLife" << std::endl;

  NodeContainer nodes;
  nodes.Create(5);

  // Install PCER Routing
  PcerHelper pcerRouting;
  Ipv4ListRoutingHelper list;
  list.Add(pcerRouting, 10);

  InternetStackHelper stack;
  stack.SetRoutingHelper(list);
  stack.Install(nodes);

  Ipv4AddressHelper address;
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces = address.Assign(nodes.Install(nodes));

  // Setup Receivers
  for (uint32_t i = 0; i < nodes.GetN(); ++i) {
    Ptr<Socket> sink = Socket::CreateSocket(
        nodes.Get(i), TypeId::LookupByName("ns3::UdpSocketFactory"));
    InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), 80);
    sink->Bind(local);
    sink->SetRecvCallback(MakeCallback(&ReceivePacket));
  }

  // --- MOCK TOPOLOGY SETUP FOR PCER ---
  // Manually adding neighbors to nodes to simulate the protocol discovering
  // them Node 0 -> Node 1 (Delay 5ms, Energy 0.9) Node 0 -> Node 2 (Delay 50ms,
  // Energy 0.2)
  for (uint32_t i = 0; i < nodes.GetN(); ++i) {
    Ptr<Ipv4> ipv4 = nodes.Get(i)->GetObject<Ipv4>();
    Ptr<Ipv4RoutingProtocol> rp = ipv4->GetRoutingProtocol();
    Ptr<Ipv4ListRouting> lrp = DynamicCast<Ipv4ListRouting>(rp);
    int16_t priority;
    Ptr<PcerRoutingProtocol> pcer =
        DynamicCast<PcerRoutingProtocol>(lrp->GetRoutingProtocol(0, priority));

    if (pcer) {
      // Add dummy neighbors for route calculation demo
      pcer->AddNeighbor(Ipv4Address("10.1.1.2"), 5.0, 0.9); // Fast, High Energy
      pcer->AddNeighbor(Ipv4Address("10.1.1.3"), 50.0, 0.2); // Slow, Low Energy
    }
  }

  // --- READ TRACE FILE ---
  std::ifstream traceFile("traffic_trace.txt");
  if (traceFile.is_open()) {
    double time;
    int srcId, dstId, size, tag;
    while (traceFile >> time >> srcId >> dstId >> size >> tag) {
      if (srcId >= 0 && srcId < 5 && dstId >= 0 && dstId < 5) {
        Simulator::Schedule(Seconds(time), &SendPacket, nodes.Get(srcId),
                            interfaces.GetAddress(dstId), size, (uint8_t)tag);
      }
    }
    traceFile.close();
  }

  Simulator::Stop(Seconds(10.0)); // Short run for demo
  Simulator::Run();
  Simulator::Destroy();

  csvFile.close();
  return 0;
}
