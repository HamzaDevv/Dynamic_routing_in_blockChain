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
  info.queue_size = 0.0;
  info.trust_score = 0.5; // Neutral start for Trust Exploration
  info.etx = 1.0;
  info.jitter = 0.0;
  info.packets_received = 0;
  info.packets_forwarded = 0;
  info.report_consistency = 1.0;
  info.load_count = 0;
  m_neighbors[neighborAddr] = info;
}

double PcerRoutingProtocol::SigmoidEnergyOverride(double battery, double threshold) {
  if (battery >= threshold) return 0.0;
  double x = (threshold - battery) / threshold * 10.0 - 5.0;
  return 1.0 / (1.0 + std::exp(-x));
}

double PcerRoutingProtocol::CalculateTrust(const NeighborInfo &neighbor) {
  uint32_t rec = std::max(neighbor.packets_received, (uint32_t)1);
  double pdr = (double)neighbor.packets_forwarded / rec;
  return 0.50 * pdr + 0.30 * neighbor.report_consistency + 0.20 * neighbor.energy;
}

double PcerRoutingProtocol::CalculateCost(uint8_t tag,
                                          const NeighborInfo &neighbor, double distanceToDest) {
  // PCER-v5 5-component cost function
  double wd, we, wt, wetx, wl;
  if (tag == 0) { // CRITICAL
    wd = 0.70; we = 0.08; wt = 0.14; wetx = 0.06; wl = 0.02;
  } else if (tag == 2) { // BULK
    wd = 0.04; we = 0.60; wt = 0.20; wetx = 0.10; wl = 0.06;
  } else { // STANDARD
    wd = 0.38; we = 0.30; wt = 0.18; wetx = 0.08; wl = 0.06;
  }

  // Hard guards
  if (neighbor.energy < 0.03) {
    return std::numeric_limits<double>::max();
  }

  double delay_cost = (neighbor.delay + distanceToDest) * wd;
  
  double e_penalty;
  if (neighbor.energy < 0.08) {
     e_penalty = std::pow(0.08 / neighbor.energy, 3) * 100.0;
  } else {
     e_penalty = (1.0 / neighbor.energy) * 2.0;
  }
  double energy_cost = e_penalty * we;

  double trust = neighbor.trust_score > 0 ? neighbor.trust_score : 0.7;
  double trust_base = (1.0 - trust) * 20.0;
  double trust_cost = trust_base * wt;

  double etx = neighbor.etx > 0 ? neighbor.etx : 1.0;
  double etx_penalty = std::max(0.0, (etx - 1.0) * 12.0);
  double etx_x_trust = etx_penalty * (1.0 - trust);
  double etx_cost = (etx_penalty + etx_x_trust) * wetx;

  double load_cost = neighbor.load_count * 0.7 * wl;

  double congestion_penalty = 0.0;
  if (neighbor.queue_size > 0.8) {
      congestion_penalty = std::pow((neighbor.queue_size - 0.8) / 0.2, 2) * 200.0;
  } else if (neighbor.queue_size > 0.5) {
      congestion_penalty = (neighbor.queue_size - 0.5) * 20.0;
  }

  return delay_cost + energy_cost + trust_cost + etx_cost + load_cost + congestion_penalty;
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

  Ipv4Address prevHop;
  auto it = m_prevBestHop.find(header.GetSource());
  if (it != m_prevBestHop.end()) {
      prevHop = it->second;
  }

  double prevCost = std::numeric_limits<double>::max();

  // For this demo, we assume the destination IS a neighbor or we just forward
  // to best neighbor. A real protocol needs a full routing table lookup.
  for (auto const &[addr, info] : m_neighbors) {
    double cost = CalculateCost(tag, info, 0.0);
    
    if (addr == prevHop) {
        prevCost = cost;
    }

    if (cost < minCost) {
      minCost = cost;
      bestNextHop = addr;
      found = true;
    }
  }

  if (found && prevHop != Ipv4Address() && prevHop != bestNextHop && prevCost < std::numeric_limits<double>::max()) {
      double improvement = (prevCost - minCost) / prevCost;
      if (improvement < m_stabilityThreshold) {
          bestNextHop = prevHop; // Hysteresis prevents oscillation
      }
  }

  if (found) {
      m_prevBestHop[header.GetSource()] = bestNextHop;
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
