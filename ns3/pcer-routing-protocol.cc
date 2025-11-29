#include "pcer-routing-protocol.h"
#include "ns3/ipv4-interface.h"
#include "ns3/ipv4.h"
#include "ns3/log.h"
#include "ns3/packet.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("PcerRoutingProtocol");
NS_OBJECT_ENSURE_REGISTERED(PcerRoutingProtocol);

TypeId PcerRoutingProtocol::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::PcerRoutingProtocol")
                          .SetParent<Ipv4RoutingProtocol>()
                          .SetGroupName("Internet")
                          .AddConstructor<PcerRoutingProtocol>();
  return tid;
}

PcerRoutingProtocol::PcerRoutingProtocol() {}

PcerRoutingProtocol::~PcerRoutingProtocol() {}

void PcerRoutingProtocol::SetIpv4(Ptr<Ipv4> ipv4) { m_ipv4 = ipv4; }

void PcerRoutingProtocol::AddNeighbor(Ipv4Address neighborAddr, double delay,
                                      double energy) {
  NeighborInfo info;
  info.addr = neighborAddr;
  info.delay = delay;
  info.energy = energy;
  // In a real protocol, we'd find the interface index dynamically
  info.interfaceIndex = 1;
  m_neighbors[neighborAddr] = info;
}

double PcerRoutingProtocol::CalculateCost(uint8_t tag,
                                          const NeighborInfo &neighbor) {
  // --- PCER CORE LOGIC ---
  double w1_delay = 1.0;
  double w2_energy = 1.0;

  if (tag == 0) { // CRITICAL
    w1_delay = 100.0;
    w2_energy = 0.0;
  } else if (tag == 2) { // BULK
    w1_delay = 0.0;
    w2_energy = 100.0;
  } else { // STANDARD
    w1_delay = 1.0;
    w2_energy = 1.0;
  }

  double energy_cost =
      (neighbor.energy > 0.0001) ? (1.0 / neighbor.energy) : 10000.0;
  return (w1_delay * neighbor.delay) + (w2_energy * energy_cost);
}

Ptr<Ipv4Route> PcerRoutingProtocol::RouteOutput(Ptr<Packet> p,
                                                const Ipv4Header &header,
                                                Ptr<NetDevice> oif,
                                                Socket::SocketErrno &sockerr) {
  NS_LOG_FUNCTION(this << p << header << oif);

  // 1. Get Tag
  PcErTag urgencyTag;
  uint8_t tag = 1; // Default Standard
  if (p->PeekPacketTag(urgencyTag)) {
    tag = urgencyTag.Get();
  }

  // 2. Find Best Neighbor (Simplified for Demo: Direct neighbors only)
  // In a full protocol, this would search the routing table for the
  // destination. Here we iterate all neighbors and pick the one with lowest
  // PCER cost.

  double minCost = std::numeric_limits<double>::max();
  Ipv4Address bestNextHop;
  bool found = false;

  // For this demo, we assume the destination IS a neighbor or we just forward
  // to best neighbor A real protocol needs a full routing table lookup.
  for (auto const &[addr, info] : m_neighbors) {
    double cost = CalculateCost(tag, info);
    if (cost < minCost) {
      minCost = cost;
      bestNextHop = addr;
      found = true;
    }
  }

  if (!found) {
    sockerr = Socket::ERROR_NOROUTETOHOST;
    return 0;
  }

  // 3. Create Route
  Ptr<Ipv4Route> route = Create<Ipv4Route>();
  route->SetDestination(header.GetDestination());
  route->SetSource(m_ipv4->GetAddress(1, 0).GetLocal()); // Assuming interface 1
  route->SetGateway(bestNextHop);
  route->SetOutputDevice(m_ipv4->GetNetDevice(1));

  return route;
}

bool PcerRoutingProtocol::RouteInput(
    Ptr<const Packet> p, const Ipv4Header &header, Ptr<const NetDevice> idev,
    UnicastForwardCallback ucb, MulticastForwardCallback mcb,
    LocalDeliverCallback lcb, ErrorCallback ecb) {
  // Simplified: If it's for us, deliver locally. Else, forward.
  if (m_ipv4->GetInterfaceForDevice(idev) >= 0) {
    uint32_t iif = m_ipv4->GetInterfaceForDevice(idev);
    if (m_ipv4->GetAddress(iif, 0).GetLocal() == header.GetDestination()) {
      lcb(p, header, iif);
      return true;
    }
  }

  // Forwarding logic would go here (call RouteOutput)
  return false;
}

void PcerRoutingProtocol::NotifyInterfaceUp(uint32_t interface) {}
void PcerRoutingProtocol::NotifyInterfaceDown(uint32_t interface) {}
void PcerRoutingProtocol::NotifyAddAddress(uint32_t interface,
                                           Ipv4InterfaceAddress address) {}
void PcerRoutingProtocol::NotifyRemoveAddress(uint32_t interface,
                                              Ipv4InterfaceAddress address) {}
void PcerRoutingProtocol::PrintRoutingTable(Ptr<OutputStreamWrapper> stream,
                                            Time::Unit unit) const {}

} // namespace ns3
