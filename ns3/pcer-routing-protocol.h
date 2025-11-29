#ifndef PCER_ROUTING_PROTOCOL_H
#define PCER_ROUTING_PROTOCOL_H

#include "ns3/ipv4-route.h"
#include "ns3/ipv4-routing-protocol.h"
#include "ns3/node.h"
#include "ns3/random-variable-stream.h"
#include "pcer_tag.h"
#include <map>

namespace ns3 {

/**
 * @brief Priority-Coupled Elastic Routing (PCER) Protocol
 *
 * This is a simplified routing protocol for demonstration purposes.
 * It assumes a static topology where costs are known/calculated based on PCER
 * metrics.
 */
class PcerRoutingProtocol : public Ipv4RoutingProtocol {
public:
  static TypeId GetTypeId(void);

  PcerRoutingProtocol();
  virtual ~PcerRoutingProtocol();

  // Ipv4RoutingProtocol methods
  virtual Ptr<Ipv4Route> RouteOutput(Ptr<Packet> p, const Ipv4Header &header,
                                     Ptr<NetDevice> oif,
                                     Socket::SocketErrno &sockerr);
  virtual bool RouteInput(Ptr<const Packet> p, const Ipv4Header &header,
                          Ptr<const NetDevice> idev, UnicastForwardCallback ucb,
                          MulticastForwardCallback mcb,
                          LocalDeliverCallback lcb, ErrorCallback ecb);
  virtual void NotifyInterfaceUp(uint32_t interface);
  virtual void NotifyInterfaceDown(uint32_t interface);
  virtual void NotifyAddAddress(uint32_t interface,
                                Ipv4InterfaceAddress address);
  virtual void NotifyRemoveAddress(uint32_t interface,
                                   Ipv4InterfaceAddress address);
  virtual void SetIpv4(Ptr<Ipv4> ipv4);
  virtual void PrintRoutingTable(Ptr<OutputStreamWrapper> stream,
                                 Time::Unit unit = Time::S) const;

  // PCER Specific Methods
  void AddNeighbor(Ipv4Address neighborAddr, double delay, double energy);

private:
  struct NeighborInfo {
    Ipv4Address addr;
    double delay;
    double energy;
    uint32_t interfaceIndex;
  };

  // Calculate cost based on PCER logic
  double CalculateCost(uint8_t tag, const NeighborInfo &neighbor);

  Ptr<Ipv4> m_ipv4;
  std::map<Ipv4Address, NeighborInfo> m_neighbors; // Simplified neighbor table
};

} // namespace ns3

#endif /* PCER_ROUTING_PROTOCOL_H */
